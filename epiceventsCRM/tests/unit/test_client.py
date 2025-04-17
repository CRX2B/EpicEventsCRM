import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from epiceventsCRM.models.models import Client, User, Department
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.views.client_view import ClientView
from epiceventsCRM.utils.auth import hash_password
from epiceventsCRM.utils.permissions import PermissionError
from epiceventsCRM.tests.mocks.mock_controllers import (
    MockAuthController,
    mock_token_commercial as get_mock_commercial_token_str,
    mock_token_gestion as get_mock_gestion_token_str,
)
from epiceventsCRM.tests.mocks.mock_dao import MockClientDAO


@pytest.fixture
def test_department():
    return Department(departement_name="commercial")


@pytest.fixture
def test_commercial(test_department):
    user = User(
        id=1,  # Doit correspondre au sub du token commercial
        fullname="Commercial Test",
        email="commercial@test.com",
        password="password123",
        departement_id=test_department.id,
    )
    return user


@pytest.fixture
def test_client(test_commercial):
    client = Client(
        id=101,  # ID de test
        fullname="Test Client",
        email="client@test.com",
        phone_number="0123456789",
        enterprise="Test Company",
        sales_contact_id=test_commercial.id,
    )
    return client


@pytest.fixture
def test_client_data(test_commercial):
    return {
        "fullname": "Test Client",
        "email": "client@test.com",
        "phone_number": "0123456789",
        "enterprise": "Test Company",
        # sales_contact_id sera ajouté par le contrôleur
    }


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


class TestClientController:
    @pytest.fixture(autouse=True)
    def setup_controller(self, mock_auth_controller_fixture):
        """Injecte les mocks dans une instance du contrôleur pour les tests de cette classe."""
        self.mock_dao = MockClientDAO()
        self.mock_auth_controller = mock_auth_controller_fixture
        # Réinitialiser les mocks AVANT d'injecter et utiliser
        self.mock_dao.reset_mocks()
        self.mock_auth_controller.reset_mocks()

        self.controller = ClientController()
        self.controller.dao = self.mock_dao
        self.controller.auth_controller = self.mock_auth_controller

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_controller_create_client(
        self, mock_verify, db_session, test_client_data, test_commercial
    ):
        """Teste la création d'un client via le contrôleur avec les mocks centraux."""
        # Configurer le retour du patch et la permission AVANT l'appel
        mock_verify.return_value = {"sub": 1, "department": "commercial"}
        token = get_mock_commercial_token_str()
        self.mock_auth_controller.check_permission.return_value = True  # Simuler permission OK

        client = self.controller.create(
            token=token, db=db_session, client_data=test_client_data.copy()
        )

        assert client is not None
        mock_verify.assert_called_once_with(token)
        self.mock_dao.create_client.assert_called_once()

        # Vérifier les arguments passés à create_client
        call_args, call_kwargs = self.mock_dao.create_client.call_args
        passed_db_session = call_args[0]
        passed_client_data = call_args[1]

        assert passed_db_session == db_session
        assert passed_client_data["fullname"] == test_client_data["fullname"]
        assert passed_client_data["email"] == test_client_data["email"]
        assert passed_client_data["phone_number"] == test_client_data["phone_number"]
        assert passed_client_data["enterprise"] == test_client_data["enterprise"]
        # Vérifier que le sales_contact_id a été ajouté par le contrôleur (ID 1 du token commercial)
        assert passed_client_data["sales_contact_id"] == 1
        # Vérifier que check_permission a été appelé par le décorateur
        self.mock_auth_controller.check_permission.assert_called_with(token, "create_client")

    def test_get_client(self, db_session, test_client, test_commercial):
        """Teste la récupération d'un client avec les mocks centraux."""
        token = get_mock_commercial_token_str()
        # Configurer la permission AVANT l'appel
        self.mock_auth_controller.check_permission.return_value = True
        # Préparer le mock DAO pour retourner le client de test
        self.mock_dao._data[test_client.id] = test_client
        self.mock_dao.get.return_value = test_client

        client_result = self.controller.get(token=token, db=db_session, entity_id=test_client.id)

        assert client_result is not None
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_auth_controller.check_permission.assert_called_with(token, "read_client")
        assert client_result.id == test_client.id
        assert client_result.email == test_client.email

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_create_client_missing_fields(self, mock_verify, db_session, test_commercial):
        """Teste la création d'un client avec des champs manquants."""
        mock_verify.return_value = {"sub": 1, "department": "commercial"}
        token = get_mock_commercial_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        client_data = {"fullname": "Test Client"}  # Données incomplètes

        client = self.controller.create(token, db_session, client_data)
        assert client is None  # Ou vérifier si une ValueError est levée
        self.mock_auth_controller.check_permission.assert_called_once_with(token, "create_client")
        self.mock_dao.create_client.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_create_client_permission_denied(self, mock_verify, db_session, test_client_data):
        """Teste la création d'un client sans permission."""
        mock_verify.return_value = {"sub": 99, "department": "support"}  # Utilisateur non autorisé
        token = "support_token"
        self.mock_auth_controller.check_permission.return_value = False

        with pytest.raises(PermissionError):
            self.controller.create(token, db_session, test_client_data.copy())

        self.mock_auth_controller.check_permission.assert_called_once_with(token, "create_client")
        self.mock_dao.create_client.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_success(self, mock_verify, db_session, test_client):
        """Teste la mise à jour réussie d'un client."""
        user_id = test_client.sales_contact_id
        mock_verify.return_value = {
            "sub": user_id,
            "department": "commercial",
        }  # Commercial propriétaire
        token = get_mock_commercial_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        # Mettre client dans _data pour que _update_client_impl le trouve
        self.mock_dao._data[test_client.id] = test_client
        self.mock_dao.get.return_value = test_client  # Garder pour l'appel get du contrôleur
        self.mock_dao.update_client.return_value = test_client

        update_data = {"fullname": "Updated Client Name"}
        result = self.controller.update_client(db_session, token, test_client.id, update_data)

        assert result is not None
        assert result.id == test_client.id
        self.mock_auth_controller.check_permission.assert_called_once_with(token, "update_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_dao.update_client.assert_called_once_with(db_session, test_client.id, update_data)

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_commercial_denied_other(self, mock_verify, db_session, test_client):
        """Teste qu'un commercial ne peut pas mettre à jour le client d'un autre."""
        other_commercial_id = 99
        mock_verify.return_value = {"sub": other_commercial_id, "department": "commercial"}
        token = "other_commercial_token"
        self.mock_auth_controller.check_permission.return_value = True  # Permission de base OK
        self.mock_dao.get.return_value = test_client  # Le client existe, appartient à user 1

        update_data = {"fullname": "Attempt Update"}
        result = self.controller.update_client(db_session, token, test_client.id, update_data)

        assert result is None
        self.mock_auth_controller.check_permission.assert_called_once_with(token, "update_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_dao.update_client.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_gestion_updates_any(self, mock_verify, db_session, test_client):
        """Teste qu'un gestionnaire peut mettre à jour n'importe quel client."""
        gestion_user_id = 50
        mock_verify.return_value = {"sub": gestion_user_id, "department": "gestion"}
        token = get_mock_gestion_token_str()
        self.mock_auth_controller.check_permission.return_value = True  # Permission OK
        # Mettre client dans _data pour que _update_client_impl le trouve
        self.mock_dao._data[test_client.id] = test_client
        self.mock_dao.get.return_value = test_client  # Garder pour l'appel get du contrôleur
        self.mock_dao.update_client.return_value = test_client

        update_data = {"enterprise": "Gestion Updated Enterprise"}
        result = self.controller.update_client(db_session, token, test_client.id, update_data)

        assert result is not None
        self.mock_auth_controller.check_permission.assert_called_once_with(token, "update_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_dao.update_client.assert_called_once_with(db_session, test_client.id, update_data)

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_permission_denied(self, mock_verify, db_session, test_client):
        """Teste la mise à jour d'un client sans la permission de base."""
        mock_verify.return_value = {
            "sub": 10,
            "department": "support",
        }  # Support ne peut pas update
        token = "support_token"
        self.mock_auth_controller.check_permission.return_value = False

        update_data = {"fullname": "Attempt Update"}
        with pytest.raises(PermissionError):
            self.controller.update_client(db_session, token, test_client.id, update_data)

        self.mock_auth_controller.check_permission.assert_called_once_with(token, "update_client")
        self.mock_dao.get.assert_not_called()
        self.mock_dao.update_client.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_delete_client_success(self, mock_verify, db_session, test_client):
        """Teste la suppression réussie d'un client (par Gestion)."""
        mock_verify.return_value = {"sub": 50, "department": "gestion"}
        token = get_mock_gestion_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        # Mettre client dans _data pour que _delete_impl le trouve
        self.mock_dao._data[test_client.id] = test_client
        self.mock_dao.get.return_value = test_client  # Client trouvé pour l'appel get
        self.mock_dao.delete.return_value = True  # Suppression réussie

        result = self.controller.delete_client(db_session, token, test_client.id)

        assert result is True
        self.mock_auth_controller.check_permission.assert_called_once_with(token, "delete_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_dao.delete.assert_called_once_with(db_session, test_client.id)

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_delete_client_not_found(self, mock_verify, db_session):
        """Teste la suppression d'un client non trouvé."""
        mock_verify.return_value = {"sub": 50, "department": "gestion"}
        token = get_mock_gestion_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        self.mock_dao.get.return_value = None  # Client non trouvé

        result = self.controller.delete_client(db_session, token, 999)

        assert result is False
        self.mock_auth_controller.check_permission.assert_called_once_with(token, "delete_client")
        self.mock_dao.get.assert_called_once_with(db_session, 999)
        self.mock_dao.delete.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_delete_client_permission_denied(self, mock_verify, db_session, test_client):
        """Teste la suppression sans permission."""
        mock_verify.return_value = {
            "sub": 10,
            "department": "support",
        }  # Supposons support n'a pas delete
        token = "support_token"
        self.mock_auth_controller.check_permission.return_value = False  # Permission refusée

        with pytest.raises(PermissionError):
            self.controller.delete_client(db_session, token, test_client.id)

        self.mock_auth_controller.check_permission.assert_called_once_with(token, "delete_client")
        self.mock_dao.get.assert_not_called()
        self.mock_dao.delete.assert_not_called()


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
