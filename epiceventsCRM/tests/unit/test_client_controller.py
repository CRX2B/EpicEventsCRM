import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.models.models import Client, User, Department
from epiceventsCRM.utils.permissions import PermissionError
from epiceventsCRM.controllers.auth_controller import AuthController


@pytest.fixture
def test_department():
    return Department(id=1, name="commercial")


@pytest.fixture
def test_commercial(test_department):
    return User(
        id=1,
        username="test_commercial",
        email="commercial@test.com",
        department_id=test_department.id,
        department=test_department,
    )


@pytest.fixture
def mock_token():
    return "fake_token"


@pytest.fixture
def mock_auth_controller():
    auth_controller = Mock()
    auth_controller.check_permission.return_value = True
    auth_controller.verify_token.return_value = {"sub": 1, "department": "commercial"}
    auth_controller.decode_token.return_value = {"sub": 1, "department": "commercial"}
    return auth_controller


class TestClientController:
    """Tests unitaires pour le contrôleur des clients"""

    def test_create_client_success(self, mock_token, mock_auth_controller):
        # Arrange
        client_controller = ClientController()
        client_controller.auth_controller = mock_auth_controller

        mock_db = Mock()
        mock_dao = Mock()
        client_controller.dao = mock_dao

        test_client = Client(
            id=1,
            fullname="Test Client",
            email="test@client.com",
            phone_number="1234567890",
            enterprise="Test Enterprise",
            sales_contact_id=1,
        )

        mock_dao.create_client.return_value = test_client

        client_data = {
            "fullname": "Test Client",
            "email": "test@client.com",
            "phone_number": "1234567890",
            "enterprise": "Test Enterprise",
        }

        # Act
        result = client_controller.create(mock_token, mock_db, client_data)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.fullname == "Test Client"
        mock_dao.create_client.assert_called_once()

    def test_get_client_success(self, mock_token, mock_auth_controller):
        # Arrange
        client_controller = ClientController()
        client_controller.auth_controller = mock_auth_controller

        mock_db = Mock()
        mock_dao = Mock()
        client_controller.dao = mock_dao

        test_client = Client(
            id=1,
            fullname="Test Client",
            email="test@client.com",
            phone_number="1234567890",
            enterprise="Test Enterprise",
            sales_contact_id=1,
        )

        mock_dao.get.return_value = test_client

        # Act
        result = client_controller.get_client(mock_db, mock_token, 1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.fullname == "Test Client"
        mock_dao.get.assert_called_once_with(mock_db, 1)

    def test_update_client_success(self, mock_token, mock_auth_controller):
        # Arrange
        client_controller = ClientController()
        client_controller.auth_controller = mock_auth_controller

        mock_db = Mock()
        mock_dao = Mock()
        client_controller.dao = mock_dao

        test_client = Client(
            id=1,
            fullname="Test Client",
            email="test@client.com",
            phone_number="1234567890",
            enterprise="Test Enterprise",
            sales_contact_id=1,
        )

        mock_dao.get.return_value = test_client
        mock_dao.update_client.return_value = test_client

        update_data = {"fullname": "Updated Client"}

        # Act
        result = client_controller.update_client(mock_db, mock_token, 1, update_data)

        # Assert
        assert result is not None
        assert result.id == 1
        mock_dao.update_client.assert_called_once_with(mock_db, 1, update_data)

    def test_create_client_missing_fields(self, mock_token, mock_auth_controller):
        # Arrange
        client_controller = ClientController()
        client_controller.auth_controller = mock_auth_controller

        mock_db = Mock()
        client_data = {"fullname": "Test Client"}  # Données incomplètes

        # Act
        result = client_controller.create(mock_token, mock_db, client_data)

        # Assert
        assert result is None

    def test_get_client_without_permission(self, mock_token):
        # Arrange
        client_controller = ClientController()
        mock_auth_controller = Mock()
        mock_auth_controller.check_permission.return_value = False
        client_controller.auth_controller = mock_auth_controller

        mock_db = Mock()

        # Act
        result = client_controller.get_client(mock_db, mock_token, 1)

        # Assert
        assert result is None

    def test_get_client_success(self, mock_token, mock_auth_controller):
        """Test de récupération d'un client"""
        # Créer un vrai objet Client pour le retour
        test_client = Client(id=1, fullname="Test Client", email="client@test.com")

        # Mock du DAO
        mock_dao = Mock()
        mock_dao.get.return_value = test_client

        # Mock de la session de base de données
        mock_db = Mock()

        # Création du contrôleur avec les mocks
        controller = ClientController()
        controller.dao = mock_dao
        controller.auth_controller = mock_auth_controller

        # Appel de la méthode get
        result = controller.get(mock_token, mock_db, 1)

        # Vérifications
        assert result is not None
        assert result.id == 1
        assert result.fullname == "Test Client"
        mock_dao.get.assert_called_once_with(mock_db, 1)
        mock_auth_controller.check_permission.assert_called_once_with(mock_token, "read_client")

    def test_update_client_success(self, mock_token, mock_auth_controller):
        """Test de mise à jour d'un client"""
        # Créer des vrais objets Client pour le test
        existing_client = Client(id=1, fullname="Old Name", email="old@test.com")
        updated_client = Client(id=1, fullname="New Name", email="new@test.com")

        # Mock du DAO
        mock_dao = Mock()
        mock_dao.get.return_value = existing_client
        mock_dao.update.return_value = updated_client

        # Mock de la session de base de données
        mock_db = Mock()

        # Création du contrôleur avec les mocks
        controller = ClientController()
        controller.dao = mock_dao
        controller.auth_controller = mock_auth_controller

        # Données de mise à jour
        update_data = {"fullname": "New Name", "email": "new@test.com"}

        # Appel de la méthode update
        result = controller.update(mock_token, mock_db, 1, update_data)

        # Vérifications
        assert result is not None
        assert result.fullname == "New Name"
        assert result.email == "new@test.com"
        mock_dao.update.assert_called_once_with(mock_db, existing_client, update_data)
        mock_auth_controller.check_permission.assert_called_once_with(mock_token, "update_client")
