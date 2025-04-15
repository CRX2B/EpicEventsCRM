import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from epiceventsCRM.models.models import Client, User, Department
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.views.client_view import ClientView
from epiceventsCRM.utils.auth import hash_password
from epiceventsCRM.utils.permissions import PermissionError
from epiceventsCRM.controllers.auth_controller import AuthController


@pytest.fixture
def test_department():
    return Department(departement_name="commercial")


@pytest.fixture
def test_commercial(test_department):
    return User(
        id=1,
        fullname="Commercial Test",
        email="commercial@test.com",
        password="password123",
        departement_id=test_department.id,
    )


@pytest.fixture
def test_client(test_commercial):
    return Client(
        fullname="Test Client",
        email="client@test.com",
        phone_number="0123456789",
        enterprise="Test Company",
        sales_contact_id=test_commercial.id,
    )


@pytest.fixture
def test_client_data(test_commercial):
    return {
        "fullname": "Test Client",
        "email": "client@test.com",
        "phone_number": "0123456789",
        "enterprise": "Test Company",
        "sales_contact_id": test_commercial.id,
    }


@pytest.fixture
def mock_token_commercial():
    # Simuler un token JWT valide
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImRlcGFydG1lbnRfaWQiOjF9.1234567890"


@pytest.fixture
def mock_auth_controller():
    auth_controller = Mock(spec=AuthController)
    # Configuration explicite des méthodes mock
    auth_controller.check_permission = Mock(return_value=True)
    auth_controller.verify_token = Mock(return_value={"sub": 1, "departement_id": 1})
    auth_controller.decode_token = Mock(return_value={"sub": 1, "departement_id": 1})
    return auth_controller


class TestClientModel:
    """Tests unitaires pour le modèle Client"""

    def test_client_creation(self):
        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number="0123456789",
            enterprise="Test Company",
        )
        assert client.fullname == "Client Test"
        assert client.email == "client@test.com"
        assert client.enterprise == "Test Company"


class MockClientDAO:
    def __init__(self, model_class):
        self.model_class = model_class
        self.clients = []
        self.next_id = 1

    def create_client(self, db, client_data):
        # Ajouter les dates de création et de mise à jour
        client_data = client_data.copy()  # Créer une copie pour ne pas modifier l'original
        client_data["create_date"] = datetime.now()
        client_data["update_date"] = datetime.now()

        # Créer un nouvel ID
        client_data["id"] = self.next_id
        self.next_id += 1

        # Créer l'instance du client
        client = self.model_class(**client_data)
        self.clients.append(client)
        return client

    def get(self, db, client_id):
        return next((c for c in self.clients if c.id == client_id), None)

    def get_all(self, db):
        return self.clients

    def get_by_commercial(self, db, commercial_id):
        return [c for c in self.clients if c.sales_contact_id == commercial_id]

    def update(self, db, client_id, client_data):
        client = self.get(db, client_id)
        if client:
            for key, value in client_data.items():
                setattr(client, key, value)
        return client

    def delete(self, db, client_id):
        client = self.get(db, client_id)
        if client:
            self.clients.remove(client)
            return True
        return False


class TestClientDAO:
    def test_create_client(self, db_session, test_commercial):
        dao = ClientDAO()
        client_data = {
            "fullname": "Test Client",
            "email": "client@test.com",
            "phone_number": "0123456789",
            "enterprise": "Test Company",
            "sales_contact_id": test_commercial.id,
        }
        client = dao.create(db_session, client_data)
        assert client.fullname == "Test Client"
        assert client.email == "client@test.com"
        assert client.sales_contact_id == test_commercial.id

    def test_get_client(self, db_session, test_commercial):
        dao = ClientDAO()
        client_data = {
            "fullname": "Test Client",
            "email": "client@test.com",
            "phone_number": "0123456789",
            "enterprise": "Test Company",
            "sales_contact_id": test_commercial.id,
        }
        client = dao.create(db_session, client_data)
        retrieved_client = dao.get(db_session, client.id)
        assert retrieved_client.id == client.id
        assert retrieved_client.email == "client@test.com"

    def test_update_client(self, db_session, test_commercial):
        dao = ClientDAO()
        client_data = {
            "fullname": "Test Client",
            "email": "client@test.com",
            "phone_number": "0123456789",
            "enterprise": "Test Company",
            "sales_contact_id": test_commercial.id,
        }
        client = dao.create(db_session, client_data)
        client = dao.get(db_session, client.id)  # Récupérer l'objet client complet
        updated_client = dao.update(
            db_session, client, {"fullname": "Updated Client", "email": "updated@test.com"}
        )
        assert updated_client.fullname == "Updated Client"
        assert updated_client.email == "updated@test.com"

    def test_get_by_commercial(self, db_session, test_commercial):
        dao = ClientDAO()

        # Créer plusieurs clients pour le même commercial
        clients_created = []
        for i in range(3):
            client_data = {
                "fullname": f"Test Client {i}",
                "email": f"client{i}@test.com",
                "phone_number": f"012345678{i}",
                "enterprise": f"Test Company {i}",
                "sales_contact_id": test_commercial.id,
            }
            client = dao.create(db_session, client_data)
            clients_created.append(client)

        # Utiliser get_all et filtrer manuellement
        all_clients, total = dao.get_all(db_session)
        clients = [c for c in all_clients if c.sales_contact_id == test_commercial.id]
        assert len(clients) == 3
        assert all(c.sales_contact_id == test_commercial.id for c in clients)


class TestClientController:
    def test_controller_create_client(
        self, db_session, test_commercial, mock_token_commercial, mock_auth_controller
    ):
        # Configuration du DAO et du controller
        dao = MockClientDAO(Client)
        controller = ClientController()
        controller.dao = dao

        # Configuration explicite du auth_controller
        controller.auth_controller = mock_auth_controller

        # Vérification que le mock est correctement configuré
        assert hasattr(
            controller.auth_controller, "decode_token"
        ), "Le controller n'a pas la méthode decode_token"

        client_data = {
            "fullname": "Test Client",
            "email": "client@test.com",
            "phone_number": 123456789,
            "enterprise": "Test Company",
        }

        # Test de création du client
        client = controller.create(
            token=mock_token_commercial, db=db_session, client_data=client_data
        )

        # Vérifications
        assert client is not None
        assert client.fullname == "Test Client"
        assert client.email == "client@test.com"
        assert client.sales_contact_id == test_commercial.id

        # Vérification que decode_token a été appelé
        controller.auth_controller.decode_token.assert_called_once_with(mock_token_commercial)

    def test_get_client(self, db_session, test_client, mock_token_commercial, mock_auth_controller):
        dao = MockClientDAO(Client)
        dao.clients.append(test_client)  # Ajouter le client de test au mock DAO

        controller = ClientController()
        controller.dao = dao
        controller.auth_controller = mock_auth_controller

        client = controller.get(
            token=mock_token_commercial, db=db_session, entity_id=test_client.id
        )
        assert client.id == test_client.id
        assert client.email == test_client.email


class TestClientView:
    def test_view_display_client(self, capsys):
        view = ClientView()
        client = Client(
            id=1,
            fullname="Test Client",
            email="client@test.com",
            phone_number="0123456789",
            enterprise="Test Company",
            sales_contact_id=1,
        )

        view.display_item(client)
        captured = capsys.readouterr()
        assert "Test Client" in captured.out
        assert "client@test.com" in captured.out
        assert "Test Company" in captured.out
