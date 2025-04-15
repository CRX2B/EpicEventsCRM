import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from epiceventsCRM.models.models import Contract, Client, User
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.views.contract_view import ContractView
from epiceventsCRM.utils.permissions import PermissionError
from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.tests.mocks.mock_controllers import MockAuthController
from epiceventsCRM.tests.mocks.mock_dao import MockContractDAO, MockClientDAO


@pytest.fixture
def test_client(clients):
    """Retourne le premier client de test"""
    return clients[0]


@pytest.fixture
def test_commercial(users):
    """Retourne l'utilisateur commercial de test"""
    return users[0]


@pytest.fixture
def test_contract(contracts):
    """Retourne le premier contrat de test"""
    return contracts[0]


@pytest.fixture
def mock_token_gestion():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjIsImRlcGFydG1lbnQiOiJnZXN0aW9uIiwicGVybWlzc2lvbnMiOlsiY3JlYXRlX2NvbnRyYWN0IiwicmVhZF9jb250cmFjdCIsInVwZGF0ZV9jb250cmFjdCIsImRlbGV0ZV9jb250cmFjdCJdfQ.1234567890"


@pytest.fixture
def setup_mocks():
    """Configure les mocks pour les tests de contrats"""
    mock_auth = MockAuthController(department="gestion")
    mock_client_dao = MockClientDAO()
    mock_contract_dao = MockContractDAO(client_dao=mock_client_dao)
    
    contract_controller = ContractController()
    contract_controller.auth_controller = mock_auth
    contract_controller.dao = mock_contract_dao
    contract_controller.client_dao = mock_client_dao
    
    return contract_controller, mock_auth, mock_client_dao, mock_contract_dao


class TestContractDAO:
    def test_create_contract(self, db_session, test_client, test_commercial):
        dao = ContractDAO()
        contract_data = {
            "client_id": test_client.id,
            "amount": 1000.0,
            "remaining_amount": 500.0,
            "status": True,
        }
        contract = dao.create(db_session, contract_data)
        assert contract.client_id == test_client.id
        assert contract.amount == 1000.0
        assert contract.remaining_amount == 500.0
        assert contract.status is True

    def test_get_contract(self, db_session, test_client, test_commercial):
        dao = ContractDAO()
        contract_data = {
            "client_id": test_client.id,
            "amount": 1000.0,
            "remaining_amount": 500.0,
            "status": True,
            "sales_contact_id": test_commercial.id,
        }
        contract = dao.create(db_session, contract_data)
        retrieved_contract = dao.get(db_session, contract.id)
        assert retrieved_contract.id == contract.id
        assert retrieved_contract.client_id == test_client.id

    def test_update_status(self, db_session, test_client, test_commercial):
        dao = ContractDAO()
        contract_data = {
            "client_id": test_client.id,
            "amount": 1000.0,
            "remaining_amount": 500.0,
            "status": True,
            "sales_contact_id": test_commercial.id,
        }
        contract = dao.create(db_session, contract_data)
        updated_contract = dao.update(db_session, contract, {"status": False})
        assert updated_contract.status is False

    def test_update_remaining_amount(self, db_session, test_client, test_commercial):
        dao = ContractDAO()
        contract_data = {
            "client_id": test_client.id,
            "amount": 1000.0,
            "remaining_amount": 500.0,
            "status": True,
            "sales_contact_id": test_commercial.id,
        }
        contract = dao.create(db_session, contract_data)
        updated_contract = dao.update(db_session, contract, {"remaining_amount": 300.0})
        assert updated_contract.remaining_amount == 300.0

    def test_get_by_client(self, db_session, test_client, test_commercial):
        dao = ContractDAO()

        # Créer plusieurs contrats pour le même client
        for i in range(3):
            contract_data = {
                "client_id": test_client.id,
                "amount": 1000.0 * (i + 1),
                "remaining_amount": 500.0 * (i + 1),
                "status": True,
                "sales_contact_id": test_commercial.id,
            }
            dao.create(db_session, contract_data)

        contracts = dao.get_by_client(db_session, test_client.id)
        assert len(contracts) == 3
        assert all(c.client_id == test_client.id for c in contracts)


class TestContractController:
    def test_controller_create_contract(self, db_session, test_client, test_commercial, mock_token_gestion, setup_mocks):
        controller, _, client_dao, _ = setup_mocks
        # Ajouter le client au DAO mock avec le commercial
        test_client.sales_contact_id = test_commercial.id
        client_dao._data[test_client.id] = test_client
        
        # Test avec des données valides
        contract_data = {
            "client_id": test_client.id,
            "amount": 1000.0,
            "remaining_amount": 1000.0,
            "status": False
        }
        contract = controller.create(mock_token_gestion, db_session, contract_data)
        assert contract is not None
        assert contract.client_id == test_client.id
        assert contract.amount == 1000.0
        assert contract.remaining_amount == 1000.0
        assert contract.status is False
        assert contract.sales_contact_id == test_commercial.id

    def test_create_contract_method(self, db_session, test_client, test_commercial, mock_token_gestion, setup_mocks):
        controller, _, client_dao, _ = setup_mocks
        # Ajouter le client au DAO mock avec le commercial
        test_client.sales_contact_id = test_commercial.id
        client_dao._data[test_client.id] = test_client
        
        # Test avec des données valides
        contract_data = {
            "client_id": test_client.id,
            "amount": 1000.0,
            "remaining_amount": 1000.0,
            "status": False
        }
        contract = controller.create(mock_token_gestion, db_session, contract_data)
        assert contract is not None
        assert contract.client_id == test_client.id
        assert contract.amount == 1000.0
        assert contract.remaining_amount == 1000.0
        assert contract.status is False
        assert contract.sales_contact_id == test_commercial.id

        # Test avec un client inexistant
        contract_data = {
            "client_id": 99999,
            "amount": 1000.0,
            "remaining_amount": 1000.0,
            "status": False
        }
        contract = controller.create(mock_token_gestion, db_session, contract_data)
        assert contract is None

    def test_get_contract(self, db_session, test_contract, mock_token_gestion, setup_mocks):
        controller, _, _, dao = setup_mocks
        # Ajouter le contrat au DAO mock
        dao._data[test_contract.id] = test_contract

        contract = controller.get(mock_token_gestion, db_session, test_contract.id)
        assert contract.id == test_contract.id
        assert contract.client_id == test_contract.client_id

    def test_update_contract(self, db_session, test_contract, mock_token_gestion, setup_mocks):
        controller, _, _, dao = setup_mocks
        # Ajouter le contrat au DAO mock
        dao._data[test_contract.id] = test_contract

        # Test de mise à jour du statut
        update_data = {"status": True}
        updated_contract = controller.update_contract(
            mock_token_gestion, db_session, test_contract.id, update_data
        )
        assert updated_contract is not None
        assert updated_contract.status is True

        # Test de mise à jour du montant
        update_data = {"amount": 2000.0, "remaining_amount": 2000.0}
        updated_contract = controller.update_contract(
            mock_token_gestion, db_session, test_contract.id, update_data
        )
        assert updated_contract is not None
        assert updated_contract.amount == 2000.0
        assert updated_contract.remaining_amount == 2000.0

        # Test de mise à jour multiple
        update_data = {"status": False, "amount": 3000.0, "remaining_amount": 3000.0}
        updated_contract = controller.update_contract(
            mock_token_gestion, db_session, test_contract.id, update_data
        )
        assert updated_contract is not None
        assert updated_contract.status is False
        assert updated_contract.amount == 3000.0
        assert updated_contract.remaining_amount == 3000.0

        # Test avec un contrat inexistant
        updated_contract = controller.update_contract(
            mock_token_gestion, db_session, 99999, {"status": True}  # ID inexistant
        )
        assert updated_contract is None

        # Test avec un token invalide
        with pytest.raises(PermissionError):
            controller.update_contract(
                "invalid_token", db_session, test_contract.id, {"status": True}
            )

    def test_get_contracts_by_client(self, db_session, test_client, test_commercial, mock_token_gestion, setup_mocks):
        controller, _, client_dao, dao = setup_mocks
        # Ajouter le client au DAO mock
        client_dao._data[test_client.id] = test_client
        
        # Créer plusieurs contrats pour le même client
        for i in range(3):
            contract_data = {
                "client_id": test_client.id,
                "amount": 1000.0 * (i + 1),
                "remaining_amount": 500.0 * (i + 1),
                "status": True,
                "sales_contact_id": test_commercial.id,
            }
            dao.create(db_session, contract_data)

        contracts = controller.get_contracts_by_client(mock_token_gestion, db_session, test_client.id)
        assert len(contracts) == 3
        assert all(c.client_id == test_client.id for c in contracts)

    def test_get_contracts_by_commercial(self, db_session, test_client, test_commercial, mock_token_gestion, setup_mocks):
        controller, _, client_dao, dao = setup_mocks
        # Ajouter le client au DAO mock avec le commercial
        test_client.sales_contact_id = test_commercial.id
        client_dao._data[test_client.id] = test_client

        # Créer un token pour le commercial
        mock_token_commercial = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImRlcGFydG1lbnQiOiJjb21tZXJjaWFsIiwicGVybWlzc2lvbnMiOlsicmVhZF9jb250cmFjdCJdfQ.1234567890"

        # Créer plusieurs contrats pour le même commercial
        for i in range(3):
            contract_data = {
                "client_id": test_client.id,
                "amount": 1000.0 * (i + 1),
                "remaining_amount": 500.0 * (i + 1),
                "status": True
            }
            dao.create(db_session, contract_data)

        contracts = controller.get_contracts_by_commercial(mock_token_commercial, db_session)
        assert len(contracts) == 3
        assert all(c.sales_contact_id == test_commercial.id for c in contracts)


class TestContractView:
    def test_view_display_contract(self, capsys):
        view = ContractView()
        contract = Contract(
            id=1,
            client_id=1,
            amount=1000.0,
            remaining_amount=500.0,
            status=True,
            sales_contact_id=1,
        )

        view.display_item(contract)
        captured = capsys.readouterr()
        assert "1000.0" in captured.out
        assert "500.0" in captured.out
        assert "Signé" in captured.out
