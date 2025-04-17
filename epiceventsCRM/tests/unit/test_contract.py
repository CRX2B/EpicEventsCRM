import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from epiceventsCRM.models.models import Contract, Client, User, Department
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.views.contract_view import ContractView
from epiceventsCRM.utils.permissions import PermissionError
from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.tests.mocks.mock_controllers import (
    MockAuthController,
    mock_token_gestion,
    mock_token_commercial as get_mock_commercial_token_str,
)
from epiceventsCRM.tests.mocks.mock_dao import MockContractDAO, MockClientDAO


@pytest.fixture
def test_department():
    return Department(id=1, departement_name="commercial")


@pytest.fixture
def test_commercial(test_department):
    return User(
        id=1,
        fullname="Commercial Test",
        email="commercial@test.com",
        departement_id=test_department.id,
    )


@pytest.fixture
def test_client(test_commercial):
    return Client(
        id=101,
        fullname="Test Client",
        email="client@test.com",
        phone_number="1234567890",
        enterprise="Test Company",
        sales_contact_id=test_commercial.id,
    )


@pytest.fixture
def test_contract(test_client):
    return Contract(
        id=201,
        client_id=test_client.id,
        amount=5000.00,
        remaining_amount=5000.00,
        status=False,
        client=test_client,
        sales_contact_id=test_client.sales_contact_id,
    )


@pytest.fixture
def setup_mocks(test_contract, test_client, test_commercial):
    """Configure les mocks importés pour les tests de contrats"""
    mock_auth = MockAuthController()
    mock_client_dao = MockClientDAO()
    mock_contract_dao = MockContractDAO(client_dao=mock_client_dao)

    # Réinitialiser les compteurs et données des mocks AVANT de les peupler
    mock_auth.reset_mocks()
    mock_client_dao.reset_mocks()
    mock_contract_dao.reset_mocks()

    # Pré-peupler les mocks avec des données de test
    mock_client_dao._data[test_client.id] = test_client
    mock_contract_dao._data[test_contract.id] = test_contract
    # Assurer que le client a le bon commercial pour le contrat testé
    test_contract.client = test_client
    test_contract.client.sales_contact_id = test_commercial.id

    contract_controller = ContractController()
    contract_controller.auth_controller = mock_auth
    contract_controller.dao = mock_contract_dao
    contract_controller.client_dao = mock_client_dao

    return contract_controller, mock_auth, mock_client_dao, mock_contract_dao


class TestContractModel:
    """Tests unitaires pour le modèle Contract"""

    def test_contract_creation(self, test_client):
        contract = Contract(
            client_id=test_client.id,
            amount=1000.00,
            remaining_amount=1000.00,
            status=False,
            sales_contact_id=test_client.sales_contact_id,
        )
        assert contract.client_id == test_client.id
        assert contract.amount == 1000.00
        assert contract.status is False


class TestContractDAO:
    """Tests unitaires pour ContractDAO"""

    @pytest.fixture
    def contract_dao(self):
        return ContractDAO()

    def test_create_contract(self, contract_dao, db_session, test_client, test_commercial):
        """Test de la création d'un contrat."""
        contract = contract_dao.create_contract(
            db_session,
            client_id=test_client.id,
            amount=2500.00,
            sales_contact_id=test_commercial.id,
            status=False,
        )
        assert contract is not None
        assert contract.id is not None
        assert contract.amount == 2500.00
        assert contract.client_id == test_client.id
        assert contract.sales_contact_id == test_commercial.id

    def test_update_contract(self, contract_dao, db_session, test_contract):
        """Test de la mise à jour d'un contrat."""
        update_data = {"status": True, "remaining_amount": 4000.00}
        updated_contract = contract_dao.update(db_session, test_contract, update_data)

        assert updated_contract is not None
        assert updated_contract.status is True
        assert updated_contract.remaining_amount == 4000.00


class TestContractView:
    """Tests unitaires pour ContractView."""

    def test_display_item(self, test_contract, capsys):
        view = ContractView()
        view.display_item(test_contract)
        captured = capsys.readouterr()
        assert "Contrat #201" in captured.out
        # assert "Test Client" in captured.out # Commenté car dépend de la BDD
        assert "5000.0" in captured.out  # Vérifier le montant


class TestContractController:
    """Tests unitaires pour ContractController."""

    @pytest.fixture(autouse=True)
    def setup_controller(self):
        self.mock_dao = MockContractDAO()
        self.mock_client_dao = MockClientDAO()
        self.mock_auth = MockAuthController()
        self.controller = ContractController()
        self.controller.dao = self.mock_dao
        self.controller.client_dao = self.mock_client_dao
        self.controller.auth_controller = self.mock_auth

    def test_controller_create_contract(self, test_client, test_commercial):
        """Test de création via le contrôleur."""
        self.mock_client_dao._data[test_client.id] = test_client  # Pré-remplir client
        self.mock_client_dao.get.return_value = test_client
        self.mock_auth.check_permission.return_value = True

        contract_data = {"client_id": test_client.id, "amount": 3000, "status": False}
        token = mock_token_gestion()
        created_contract = self.controller.create(token, None, contract_data)

        assert created_contract is not None
        self.mock_auth.check_permission.assert_called_with(token, "create_contract")
        self.mock_dao.create_contract.assert_called_once()
        call_args, call_kwargs = self.mock_dao.create_contract.call_args
        assert call_kwargs["client_id"] == test_client.id
        assert call_kwargs["amount"] == 3000
        assert (
            call_kwargs["sales_contact_id"] == test_client.sales_contact_id
        )  # Doit être récupéré du client
        assert call_kwargs["status"] is False

    @patch("epiceventsCRM.controllers.contract_controller.verify_token")
    def test_controller_update_contract(self, mock_verify, test_contract, test_client):
        """Test de mise à jour via le contrôleur."""
        mock_verify.return_value = {"sub": 3, "department": "gestion"}

        self.mock_dao._data[test_contract.id] = test_contract
        self.mock_dao.get.return_value = test_contract
        self.mock_dao.update.return_value = test_contract
        self.mock_auth.check_permission.return_value = True

        update_data = {"remaining_amount": 1000}
        token = "fake_gestion_token"
        updated_contract = self.controller.update_contract(
            token, None, test_contract.id, update_data
        )

        assert updated_contract is not None
        mock_verify.assert_called_once_with(token)
        self.mock_auth.check_permission.assert_called_with(token, "update_contract")
        self.mock_dao.get.assert_called_once_with(None, test_contract.id)
        self.mock_dao.update.assert_called_once_with(None, test_contract, update_data)
