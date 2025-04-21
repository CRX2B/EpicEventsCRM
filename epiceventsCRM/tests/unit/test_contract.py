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
from sqlalchemy.exc import NoResultFound


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
        create_date=datetime.now(),
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
        create_date=datetime.now(),
    )


@pytest.fixture
def setup_mocks(test_contract, test_client, test_commercial):
    """Configure les mocks importés pour les tests de contrats"""
    mock_auth = MockAuthController()
    mock_client_dao = MockClientDAO()
    mock_contract_dao = MockContractDAO(client_dao=mock_client_dao)

    mock_auth.reset_mocks()
    mock_client_dao.reset_mocks()
    mock_contract_dao.reset_mocks()

    mock_client_dao._data[test_client.id] = test_client
    mock_contract_dao._data[test_contract.id] = test_contract
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
        assert "5000.0" in captured.out


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
        self.mock_dao.reset_mocks()
        self.mock_client_dao.reset_mocks()
        self.mock_auth.reset_mocks()

    def test_controller_create_contract_success(self, test_client, test_commercial):
        self.mock_client_dao._data[test_client.id] = test_client
        self.mock_client_dao.get.return_value = test_client
        self.mock_auth.check_permission.return_value = True

        expected_id = self.mock_dao.next_id
        mock_created = Mock(spec=Contract, id=expected_id)
        self.mock_dao.create_contract.return_value = mock_created

        contract_data = {"client_id": test_client.id, "amount": 3000, "status": False}
        token = mock_token_gestion()
        created_contract = self.controller.create(token, None, contract_data)

        assert created_contract is not None
        assert created_contract.id == expected_id
        self.mock_auth.check_permission.assert_called_with(token, "create_contract")
        self.mock_client_dao.get.assert_called_once_with(None, test_client.id)
        self.mock_dao.create_contract.assert_called_once()
        _, call_kwargs = self.mock_dao.create_contract.call_args
        assert call_kwargs["sales_contact_id"] == test_commercial.id

    @pytest.mark.parametrize(
        "missing_data",
        [
            {"amount": 3000},
            {"client_id": 101},
        ],
    )
    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_controller_create_contract_missing_data(self, mock_capture, missing_data):
        self.mock_auth.check_permission.return_value = True
        token = mock_token_gestion()
        result = self.controller.create(token, None, missing_data)
        assert result is None
        mock_capture.assert_called_with(
            "Données manquantes pour la création du contrat (client_id ou amount)",
            level="warning",
        )
        self.mock_dao.create_contract.assert_not_called()

    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_controller_create_contract_client_not_found(self, mock_capture):
        self.mock_auth.check_permission.return_value = True
        self.mock_client_dao.get.return_value = None
        token = mock_token_gestion()
        contract_data = {"client_id": 999, "amount": 3000}

        result = self.controller.create(token, None, contract_data)
        assert result is None
        mock_capture.assert_called_with(
            f"Client avec ID 999 non trouvé lors de la création du contrat.",
            level="warning",
        )
        self.mock_client_dao.get.assert_called_once_with(None, 999)
        self.mock_dao.create_contract.assert_not_called()

    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_controller_create_contract_client_no_commercial(self, mock_capture, test_client):
        test_client.sales_contact_id = None
        self.mock_client_dao._data[test_client.id] = test_client
        self.mock_client_dao.get.return_value = test_client
        self.mock_auth.check_permission.return_value = True
        token = mock_token_gestion()
        contract_data = {"client_id": test_client.id, "amount": 3000}

        result = self.controller.create(token, None, contract_data)
        assert result is None
        mock_capture.assert_called_with(
            f"Le client {test_client.id} n'a pas de commercial assigné.", level="warning"
        )
        self.mock_client_dao.get.assert_called_once_with(None, test_client.id)
        self.mock_dao.create_contract.assert_not_called()

    @patch("epiceventsCRM.controllers.contract_controller.verify_token")
    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_controller_update_contract_success_gestion(
        self, mock_capture, mock_verify, test_contract
    ):
        mock_verify.return_value = {"sub": 3, "department": "gestion"}
        self.mock_dao._data[test_contract.id] = test_contract
        self.mock_dao.get.return_value = test_contract
        updated_mock = Mock(spec=Contract, id=test_contract.id, status=True, remaining_amount=1000)
        self.mock_dao.update.return_value = updated_mock
        self.mock_auth.check_permission.return_value = True

        update_data = {"remaining_amount": 1000, "status": True}
        token = "fake_gestion_token"
        updated_contract = self.controller.update_contract(
            token, None, test_contract.id, update_data
        )

        mock_capture.assert_any_call(
            f"Tentative de mise à jour du contrat {test_contract.id} par l'utilisateur 3 (département: gestion)",
            level="info",
        )

        signature_log_found = any(
            f"Contrat {test_contract.id} signé" in call.args[0]
            for call in mock_capture.call_args_list
            if call.args
        )
        assert signature_log_found, f"Log de signature pour contrat {test_contract.id} non trouvé"

    @patch("epiceventsCRM.controllers.contract_controller.verify_token")
    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_controller_update_contract_commercial_owner_success(
        self, mock_capture, mock_verify, test_contract, test_commercial, test_client
    ):
        test_client.sales_contact_id = test_commercial.id
        test_contract.client = test_client
        test_contract.sales_contact_id = test_commercial.id

        mock_verify.return_value = {"sub": test_commercial.id, "department": "commercial"}
        self.mock_dao._data[test_contract.id] = test_contract
        self.mock_dao.get.return_value = test_contract
        self.mock_dao.update.return_value = test_contract
        self.mock_auth.check_permission.return_value = True

        update_data = {"remaining_amount": 2000}
        token = get_mock_commercial_token_str()
        updated_contract = self.controller.update_contract(
            token, None, test_contract.id, update_data
        )

        assert updated_contract is not None
        self.mock_auth.check_permission.assert_called_with(token, "update_contract")
        self.mock_dao.get.assert_called_once_with(None, test_contract.id)
        self.mock_dao.update.assert_called_once_with(None, test_contract, update_data)
        mock_capture.assert_any_call(
            f"Tentative de mise à jour du contrat {test_contract.id} par l'utilisateur {test_commercial.id} (département: commercial)",
            level="info",
        )

    @patch("epiceventsCRM.controllers.contract_controller.verify_token")
    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_controller_update_contract_commercial_not_owner_fail(
        self, mock_capture, mock_verify, test_contract, test_client
    ):
        other_commercial_id = 99
        test_client.sales_contact_id = other_commercial_id
        test_contract.client = test_client
        test_contract.sales_contact_id = other_commercial_id

        mock_verify.return_value = {"sub": 1, "department": "commercial"}
        self.mock_dao._data[test_contract.id] = test_contract
        self.mock_dao.get.return_value = test_contract
        self.mock_auth.check_permission.return_value = True

        update_data = {"remaining_amount": 2000}
        token = "fake_commercial_token_id_1"
        result = self.controller.update_contract(token, None, test_contract.id, update_data)

        assert result is None
        self.mock_auth.check_permission.assert_called_with(token, "update_contract")
        self.mock_dao.get.assert_called_once_with(None, test_contract.id)
        mock_capture.assert_any_call(
            f"Accès refusé: le commercial 1 n'est pas associé au client du contrat {test_contract.id}",
            level="warning",
        )
        self.mock_dao.update.assert_not_called()

    @patch("epiceventsCRM.controllers.contract_controller.verify_token")
    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_controller_update_contract_unauthorized_department_fail(
        self, mock_capture, mock_verify, test_contract
    ):
        mock_verify.return_value = {"sub": 5, "department": "support"}
        self.mock_dao._data[test_contract.id] = test_contract
        self.mock_dao.get.return_value = test_contract
        self.mock_auth.check_permission.return_value = True

        update_data = {"remaining_amount": 2000}
        token = "fake_support_token"
        result = self.controller.update_contract(token, None, test_contract.id, update_data)

        assert result is None
        self.mock_auth.check_permission.assert_called_with(token, "update_contract")
        self.mock_dao.get.assert_called_once_with(None, test_contract.id)
        mock_capture.assert_any_call(
            f"Accès refusé: le département support n'a pas les permissions nécessaires",
            level="warning",
        )
        self.mock_dao.update.assert_not_called()

    @patch("epiceventsCRM.controllers.contract_controller.verify_token")
    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_controller_update_contract_not_found(self, mock_capture, mock_verify):
        mock_verify.return_value = {"sub": 3, "department": "gestion"}
        self.mock_dao.get.return_value = None
        self.mock_auth.check_permission.return_value = True

        update_data = {"remaining_amount": 1000}
        token = "fake_gestion_token"
        contract_id = 999
        result = self.controller.update_contract(token, None, contract_id, update_data)

        assert result is None
        self.mock_auth.check_permission.assert_called_with(token, "update_contract")
        self.mock_dao.get.assert_called_once_with(None, contract_id)
        mock_capture.assert_any_call(
            f"Tentative de mise à jour d'un contrat inexistant: {contract_id}",
            level="warning",
        )
        self.mock_dao.update.assert_not_called()

    @patch("epiceventsCRM.controllers.contract_controller.capture_message")
    def test_get_all_filters(self, mock_capture, test_contract):
        self.mock_dao.get_all = Mock(return_value=([test_contract], 1))
        self.mock_auth.check_permission.return_value = True
        token = mock_token_gestion()

        contracts, total = self.controller.get_all(token, None, unsigned_only=True)

        assert total == 1
        assert len(contracts) == 1
        assert contracts[0].id == test_contract.id
        self.mock_dao.get_all.assert_called_once_with(
            None, page=1, page_size=10, filters={"status": False}
        )

    def test_controller_delete_contract(self, test_contract):
        self.mock_dao.get = Mock(return_value=test_contract)
        self.mock_dao.delete = Mock(return_value=True)
        self.mock_auth.check_permission.return_value = True
        token = mock_token_gestion()

        result = self.controller.delete(token, None, test_contract.id)

        assert result is True
        self.mock_auth.check_permission.assert_called_with(token, "delete_contract")
        self.mock_dao.get.assert_called_once_with(None, test_contract.id)
        self.mock_dao.delete.assert_called_once_with(None, test_contract.id)
