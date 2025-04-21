import pytest
from datetime import datetime, timedelta
from epiceventsCRM.models.models import Event, User, Department, Client, Contract
from epiceventsCRM.dao.event_dao import EventDAO
from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.views.event_view import EventView
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.user_dao import UserDAO
from unittest.mock import patch, Mock
from epiceventsCRM.tests.mocks.mock_dao import MockEventDAO, MockContractDAO, MockUserDAO
from epiceventsCRM.tests.mocks.mock_controllers import (
    mock_token_gestion as get_mock_gestion_token_str,
    mock_token_support as get_mock_support_token_str,
    MockAuthController,
)
from epiceventsCRM.utils.permissions import PermissionError
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def test_support(db_session):
    """Fixture pour créer un support de test"""
    department = Department(departement_name="support")
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)

    user = User(
        fullname="Support Test",
        email="support@test.com",
        password="password123",
        departement_id=department.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_client(db_session, test_support):
    """Fixture pour créer un client de test"""
    client = Client(
        fullname="Test Client",
        email="client@test.com",
        phone_number="1234567890",
        enterprise="Test Company",
        create_date=datetime.now(),
        sales_contact_id=test_support.id,
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


@pytest.fixture
def test_contract(db_session, test_client):
    """Fixture pour créer un contrat de test"""
    contract = Contract(
        client_id=test_client.id,
        amount=1000.00,
        remaining_amount=1000.00,
        status=False,
        create_date=datetime.now(),
        sales_contact_id=test_client.sales_contact_id,
    )
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    return contract


@pytest.fixture
def test_event_data(test_client, test_support, test_contract):
    """Fixture pour les données de test d'événement"""
    now = datetime.now()
    return {
        "name": "Test Event",
        "contract_id": test_contract.id,
        "client_id": test_contract.client_id,
        "location": "Test Location",
        "start_event": now + timedelta(days=1),
        "end_event": now + timedelta(days=1, hours=2),
        "attendees": 50,
        "notes": "Test notes",
    }


@pytest.fixture
def test_event(db_session, test_event_data):
    event = Event(**test_event_data)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


class TestEventModel:
    """Tests unitaires pour le modèle Event"""

    def test_event_creation(self):
        event = Event(
            name="Événement Test",
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Paris",
            attendees=50,
            notes="Notes de test",
        )
        assert event.name == "Événement Test"
        assert event.location == "Paris"
        assert event.attendees == 50


class TestEventDAO:
    """Tests unitaires pour le DAO Event"""

    @pytest.fixture
    def event_dao(self):
        """Fixture pour créer une instance de EventDAO"""
        return EventDAO()

    def test_get_by_id(self, event_dao, db_session, test_event_data):
        """Test de récupération d'un événement par ID."""
        event = event_dao.create_event(db_session, test_event_data)

        retrieved_event = event_dao.get(db_session, event.id)
        assert retrieved_event is not None
        assert retrieved_event.location == event.location

        event = event_dao.get(db_session, 9999)
        assert event is None

    def test_get_all(self, event_dao, db_session, test_event_data):
        """Test de récupération de tous les événements."""
        event1 = event_dao.create_event(db_session, test_event_data)

        event_data2 = test_event_data.copy()
        event_data2["location"] = "Another Location"
        event_data2["notes"] = "Different notes"
        event2 = event_dao.create_event(db_session, event_data2)

        all_events, total = event_dao.get_all(db_session)
        assert len(all_events) >= 2

        page1, total = event_dao.get_all(db_session, page=1, page_size=2)
        assert len(page1) <= 2

        event_dao.delete(db_session, event1.id)
        event_dao.delete(db_session, event2.id)

    def test_create(self, event_dao, db_session, test_contract, test_client):
        """Test de création d'un événement."""
        start_event = datetime.now() + timedelta(days=3)
        end_event = start_event + timedelta(hours=5)

        event_data = {
            "contract_id": test_contract.id,
            "name": "Test Event",
            "start_event": start_event,
            "end_event": end_event,
            "location": "Test Location Create",
            "attendees": 75,
            "notes": "Test notes creation",
        }

        event = event_dao.create_event(db_session, event_data)
        assert event is not None
        assert event.contract_id == test_contract.id
        assert event.name == "Test Event"
        assert event.location == "Test Location Create"
        assert event.attendees == 75

    def test_update(self, event_dao, db_session, test_event_data):
        """Test de mise à jour d'un événement."""
        event = event_dao.create_event(db_session, test_event_data)

        update_data = {"location": "Updated Location", "attendees": 100}

        updated_event = event_dao.update(db_session, event, update_data)

        assert updated_event is not None
        assert updated_event.id == event.id
        assert updated_event.location == "Updated Location"
        assert updated_event.attendees == 100

    def test_delete(self, event_dao, db_session, test_event_data):
        """Test de suppression d'un événement."""
        event = event_dao.create_event(db_session, test_event_data)

        assert event_dao.get(db_session, event.id) is not None

        result = event_dao.delete(db_session, event.id)

        assert result is True

        assert event_dao.get(db_session, event.id) is None

    def test_get_by_contract(self, event_dao, db_session, test_contract, test_event_data):
        """Test de récupération des événements par contrat."""
        event = event_dao.create_event(db_session, test_event_data)

        contract_events = event_dao.get_by_contract(db_session, test_contract.id)

        assert len(contract_events) > 0
        assert all(e.contract_id == test_contract.id for e in contract_events)


class TestEventView:
    """Tests unitaires pour la vue Event"""

    def test_view_display_event(self, capsys):
        """Test de l'affichage d'un événement."""
        view = EventView()
        event = Event(
            name="Test Event",
            location="Test Location",
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            attendees=50,
            notes="Test notes",
        )

        view.display_item(event)
        captured = capsys.readouterr()

        assert "Test Event" in captured.out
        assert "Test Location" in captured.out
        assert "50" in captured.out


@pytest.fixture
def setup_event_mocks(test_event_data, test_contract, test_support):
    """Configure les mocks pour les tests de EventController."""
    mock_event_dao = MockEventDAO()
    mock_contract_dao = MockContractDAO()
    mock_user_dao = MockUserDAO()
    mock_auth_controller = MockAuthController()

    mock_contract_dao._data[test_contract.id] = test_contract
    mock_user_dao._data[test_support.id] = test_support

    event_controller = EventController()
    event_controller.dao = mock_event_dao
    event_controller.contract_dao = mock_contract_dao
    event_controller.user_dao = mock_user_dao
    event_controller.auth_controller = mock_auth_controller

    initial_event_data = test_event_data.copy()
    initial_event_data["support_contact_id"] = test_support.id
    mock_event = mock_event_dao._create_impl(None, initial_event_data)
    mock_event.id = 1
    mock_event_dao._data[mock_event.id] = mock_event

    return (
        event_controller,
        mock_event_dao,
        mock_contract_dao,
        mock_user_dao,
        mock_event,
        mock_auth_controller,
    )


class TestEventController:
    """Tests unitaires pour EventController."""

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_create_event_success(
        self, mock_verify, db_session, setup_event_mocks, test_event_data
    ):
        """Teste la création réussie d'un événement."""
        mock_verify.return_value = {"sub": 1}
        token = get_mock_gestion_token_str()
        controller, dao, contract_dao, _, _, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True

        contract = controller.contract_dao.get(db_session, test_event_data["contract_id"])
        contract.status = True

        event_data = test_event_data.copy()
        created_event = controller.create(token, db_session, event_data)

        assert created_event is not None
        assert isinstance(created_event, Event)
        mock_auth.check_permission.assert_called_with(token, "create_event")
        dao.create_event.assert_called_once_with(db_session, event_data)

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_create_event_missing_field(
        self, mock_verify, db_session, setup_event_mocks, test_event_data
    ):
        """Teste l'échec de création avec un champ manquant."""
        mock_verify.return_value = {"sub": 1}
        token = get_mock_gestion_token_str()
        controller, dao, _, _, _, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True

        contract = controller.contract_dao.get(db_session, test_event_data["contract_id"])
        contract.status = True

        event_data_missing = test_event_data.copy()
        del event_data_missing["location"]

        with pytest.raises(ValueError) as excinfo:
            controller.create(token, db_session, event_data_missing)
        assert "Champ obligatoire manquant: location" in str(excinfo.value)
        mock_auth.check_permission.assert_called_with(token, "create_event")

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_create_event_contract_not_found(
        self, mock_verify, db_session, setup_event_mocks, test_event_data
    ):
        """Teste l'échec de création si le contrat n'est pas trouvé."""
        mock_verify.return_value = {"sub": 1}
        token = get_mock_gestion_token_str()
        controller, dao, _, _, _, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True

        mock_contract_dao_specific = MockContractDAO()
        mock_contract_dao_specific.get.return_value = None
        controller.contract_dao = mock_contract_dao_specific

        event_data = test_event_data.copy()
        with pytest.raises(ValueError) as excinfo:
            controller.create(token, db_session, event_data)

        expected_error = f"Contrat avec ID {event_data['contract_id']} non trouvé"
        assert str(excinfo.value) == expected_error
        mock_auth.check_permission.assert_called_with(token, "create_event")
        mock_contract_dao_specific.get.assert_called_once_with(
            db_session, event_data["contract_id"]
        )
        dao.create_event.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_create_event_contract_not_signed(
        self, mock_verify, db_session, setup_event_mocks, test_event_data
    ):
        """Teste l'échec de création si le contrat n'est pas signé."""
        mock_verify.return_value = {"sub": 1}
        token = get_mock_gestion_token_str()
        controller, dao, contract_dao, _, _, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True

        contract = controller.contract_dao.get(db_session, test_event_data["contract_id"])
        contract.status = False

        event_data = test_event_data.copy()
        with pytest.raises(ValueError) as excinfo:
            controller.create(token, db_session, event_data)
        assert f"Le contrat {contract.id} n'est pas signé" in str(excinfo.value)
        mock_auth.check_permission.assert_called_with(token, "create_event")
        dao.create_event.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_get_events_by_support_success(
        self, mock_verify, db_session, setup_event_mocks, test_support
    ):
        """Teste la récupération des événements par le support assigné."""
        mock_verify.return_value = {"sub": test_support.id}
        token = get_mock_support_token_str()
        controller, dao, _, _, mock_event, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True

        dao.get_by_support.return_value = [mock_event]

        events = controller.get_events_by_support(token, db_session)

        assert isinstance(events, list)
        assert len(events) == 1
        assert events[0] == mock_event
        mock_auth.check_permission.assert_called_with(token, "read_event")
        dao.get_by_support.assert_called_once_with(db_session, test_support.id)

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_get_events_by_support_invalid_token(self, mock_verify, db_session, setup_event_mocks):
        """Teste l'échec de récupération avec un token invalide."""
        mock_verify.return_value = None
        token = "invalid_token"
        controller, dao, _, _, _, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True

        events = controller.get_events_by_support(token, db_session)

        assert events == []

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_update_event_notes_success(
        self, mock_verify, db_session, setup_event_mocks, test_support
    ):
        """Teste la mise à jour réussie des notes par le support assigné."""
        mock_verify.return_value = {"sub": test_support.id}
        token = get_mock_support_token_str()
        controller, dao, _, _, mock_event, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True
        event_id = mock_event.id
        mock_event.support_contact_id = test_support.id
        new_notes = "Notes mises à jour."

        filtered_dict = {k: v for k, v in mock_event.__dict__.items() if not k.startswith("_sa_")}
        updated_event_mock = Event(**filtered_dict)
        updated_event_mock.notes = new_notes
        dao.update_notes.return_value = updated_event_mock
        dao.get.return_value = mock_event

        updated_event = controller.update_event_notes(token, db_session, event_id, new_notes)

        assert updated_event is not None
        assert updated_event.notes == new_notes
        mock_auth.check_permission.assert_called_with(token, "update_event")
        dao.get.assert_called_once_with(db_session, event_id)
        dao.update_notes.assert_called_once_with(db_session, event_id, new_notes)

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_update_event_notes_not_assigned_support(
        self, mock_verify, db_session, setup_event_mocks
    ):
        """Teste l'échec de mise à jour si l'utilisateur n'est pas le support assigné."""
        wrong_user_id = 999
        mock_verify.return_value = {"sub": wrong_user_id}
        token = "other_user_token"
        controller, dao, _, _, mock_event, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True
        event_id = mock_event.id
        mock_event.support_contact_id = 123
        new_notes = "Tentative de notes."

        dao.get.return_value = mock_event

        with pytest.raises(PermissionError) as excinfo:
            controller.update_event_notes(token, db_session, event_id, new_notes)
        assert "Vous n'êtes pas le support assigné" in str(excinfo.value)
        mock_auth.check_permission.assert_called_with(token, "update_event")
        dao.get.assert_called_once_with(db_session, event_id)
        dao.update_notes.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_update_event_notes_event_not_found(self, mock_verify, db_session, setup_event_mocks):
        """Teste l'échec de mise à jour si l'événement n'est pas trouvé."""
        mock_verify.return_value = {"sub": 1}
        token = get_mock_support_token_str()
        controller, dao, _, _, _, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True
        event_id = 999
        new_notes = "Notes pour rien."

        dao.get.return_value = None

        result = controller.update_event_notes(token, db_session, event_id, new_notes)

        assert result is None
        mock_auth.check_permission.assert_called_with(token, "update_event")
        dao.get.assert_called_once_with(db_session, event_id)
        dao.update_notes.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    @patch("epiceventsCRM.controllers.event_controller.capture_exception")
    @patch("epiceventsCRM.controllers.event_controller.ContractDAO")
    def test_create_event_integrity_error(
        self,
        mock_ContractDAO,
        mock_capture,
        mock_verify,
        db_session,
        setup_event_mocks,
        test_event_data,
    ):
        controller, mock_event_dao, _, mock_user_dao, _, mock_auth = setup_event_mocks

        mock_contract_dao_instance = mock_ContractDAO.return_value
        mock_signed_contract = Mock(spec=Contract, id=test_event_data["contract_id"], status=True)
        mock_contract_dao_instance.get.return_value = mock_signed_contract

        controller.dao = mock_event_dao
        controller.contract_dao = mock_contract_dao_instance

        mock_verify.return_value = {"sub": 1, "department": "commercial"}
        token = "some_token"
        mock_auth.check_permission.return_value = True

        mock_event_dao.create_event.side_effect = IntegrityError(
            "DB error", params={}, orig=Exception()
        )

        with pytest.raises(IntegrityError):
            controller.create(token, db_session, test_event_data.copy())

        mock_contract_dao_instance.get.assert_called_once_with(
            db_session, test_event_data["contract_id"]
        )
        mock_event_dao.create_event.assert_called_once()
        mock_capture.assert_called_once_with(mock_event_dao.create_event.side_effect)

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_get_all_no_support_filter(self, mock_verify, setup_event_mocks):
        """Teste get_all sans filtre spécifique au support."""
        controller, mock_event_dao, _, _, _, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        mock_verify.return_value = {"sub": 1, "department": "gestion"}

        mock_event = Mock(spec=Event)
        mock_event_dao.get_all = Mock(return_value=([mock_event], 1))

        events, total = controller.get_all(token, None)

        assert total == 1
        assert len(events) == 1
        mock_event_dao.get_all.assert_called_once_with(None, page=1, page_size=10, filters=None)

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_update_event_support_success_gestion(
        self, mock_verify, db_session, setup_event_mocks, test_support
    ):
        controller, mock_event_dao, _, mock_user_dao, _, mock_auth = setup_event_mocks
        mock_event = Mock(spec=Event, id=1)
        mock_verify.return_value = {"sub": 99, "department": "gestion"}
        token = get_mock_gestion_token_str()
        mock_auth.check_permission.return_value = True
        mock_event_dao.get.return_value = mock_event
        mock_user_dao.get.return_value = test_support
        mock_event_dao.update_support.return_value = mock_event

        result = controller.update_event_support(token, db_session, 1, test_support.id)

        assert result is not None
        assert result.id == 1
        assert result.support_contact_id == test_support.id
        mock_auth.check_permission.assert_called_with(token, "update_event")
        mock_event_dao.get.assert_called_once_with(db_session, 1)
        mock_user_dao.get.assert_called_once_with(db_session, test_support.id)
        mock_event_dao.update_support.assert_called_once_with(db_session, 1, test_support.id)

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_update_event_support_fail_not_gestion(
        self, mock_verify, db_session, setup_event_mocks, test_support
    ):
        controller, mock_event_dao, _, mock_user_dao, _, mock_auth = setup_event_mocks
        mock_event = Mock(spec=Event, id=1)
        mock_verify.return_value = {"sub": 1, "department": "commercial"}
        token = "commercial_token"
        mock_auth.check_permission.return_value = True
        mock_event_dao.get.return_value = mock_event
        mock_user_dao.get.return_value = test_support

        result = controller.update_event_support(token, db_session, 1, test_support.id)

        assert result is None
        mock_auth.check_permission.assert_called_with(token, "update_event")
        mock_event_dao.get.assert_called_once_with(db_session, 1)
        mock_user_dao.get.assert_called_once_with(db_session, test_support.id)
        mock_event_dao.update_support.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_update_event_support_event_not_found(
        self, mock_verify, db_session, setup_event_mocks, test_support
    ):
        controller, mock_event_dao, _, _, _, mock_auth = setup_event_mocks
        mock_verify.return_value = {"sub": 99, "department": "gestion"}
        token = get_mock_gestion_token_str()
        mock_auth.check_permission.return_value = True
        mock_event_dao.get.return_value = None

        result = controller.update_event_support(token, db_session, 999, test_support.id)

        assert result is None
        mock_auth.check_permission.assert_called_with(token, "update_event")
        mock_event_dao.get.assert_called_once_with(db_session, 999)
        mock_event_dao.update_support.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_update_event_support_support_user_not_found(
        self, mock_verify, db_session, setup_event_mocks
    ):
        controller, mock_event_dao, _, mock_user_dao, _, mock_auth = setup_event_mocks
        mock_event = Mock(spec=Event, id=1)
        mock_verify.return_value = {"sub": 99, "department": "gestion"}
        token = get_mock_gestion_token_str()
        mock_auth.check_permission.return_value = True
        mock_event_dao.get.return_value = mock_event
        mock_user_dao.get.return_value = None

        result = controller.update_event_support(token, db_session, 1, 999)

        assert result is None
        mock_auth.check_permission.assert_called_with(token, "update_event")
        mock_event_dao.get.assert_called_once_with(db_session, 1)
        mock_user_dao.get.assert_called_once_with(db_session, 999)
        mock_event_dao.update_support.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_update_event_notes_invalid_token(self, mock_verify, db_session, setup_event_mocks):
        controller, mock_event_dao, _, _, _, mock_auth = setup_event_mocks
        mock_event = Mock(spec=Event, id=1, support_contact_id=5)
        mock_event_dao.get.return_value = mock_event
        mock_auth.check_permission.return_value = True
        mock_verify.return_value = None
        token = "invalid_token"

        with pytest.raises(PermissionError) as excinfo:
            controller.update_event_notes(token, db_session, 1, "New notes")

        assert "Token invalide pour la mise à jour des notes." in str(excinfo.value)
        mock_auth.check_permission.assert_called_with(token, "update_event")
        mock_event_dao.get.assert_called_once_with(db_session, 1)
        mock_verify.assert_called_once_with(token)
        mock_event_dao.update_notes.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_delete_event_success_gestion(
        self, mock_verify, db_session, setup_event_mocks, test_event
    ):
        controller, mock_event_dao, _, _, _, mock_auth = setup_event_mocks
        mock_verify.return_value = {"sub": 99, "department": "gestion"}
        token = get_mock_gestion_token_str()
        mock_auth.check_permission.return_value = True
        mock_event_dao.delete.return_value = True

        result = controller.delete_event(token, db_session, test_event.id)

        assert result is True
        mock_auth.check_permission.assert_called_with(token, "delete_event")
        mock_event_dao.delete.assert_called_once_with(db_session, test_event.id)

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_delete_event_another_success_gestion(
        self, mock_verify, db_session, setup_event_mocks, test_event
    ):
        controller, mock_event_dao, _, _, _, mock_auth = setup_event_mocks
        mock_verify.return_value = {"sub": 100, "department": "gestion"}
        token = "gestion_token_2"
        mock_auth.check_permission.return_value = True
        mock_event_dao.delete.return_value = True

        result = controller.delete_event(token, db_session, test_event.id)

        assert result is True
        mock_auth.check_permission.assert_called_with(token, "delete_event")
        mock_event_dao.delete.assert_called_once_with(db_session, test_event.id)

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_delete_event_fail_commercial_department(
        self, mock_verify, db_session, setup_event_mocks, test_event
    ):
        controller, mock_event_dao, _, _, _, mock_auth = setup_event_mocks
        commercial_id = 99
        mock_verify.return_value = {"sub": commercial_id, "department": "commercial"}
        token = "commercial_token"
        mock_auth.check_permission.return_value = False

        with pytest.raises(PermissionError):
            controller.delete_event(token, db_session, test_event.id)

        mock_auth.check_permission.assert_called_with(token, "delete_event")
        mock_event_dao.get.assert_not_called()
        mock_event_dao.delete.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_delete_event_fail_support_department(
        self, mock_verify, db_session, setup_event_mocks, test_event
    ):
        controller, mock_event_dao, _, _, _, mock_auth = setup_event_mocks
        support_id = 5
        mock_verify.return_value = {"sub": support_id, "department": "support"}
        token = get_mock_support_token_str()
        mock_auth.check_permission.return_value = False

        with pytest.raises(PermissionError):
            controller.delete_event(token, db_session, test_event.id)

        mock_auth.check_permission.assert_called_with(token, "delete_event")
        mock_event_dao.get.assert_not_called()
        mock_event_dao.delete.assert_not_called()

    @patch("epiceventsCRM.controllers.event_controller.verify_token")
    def test_delete_event_not_found(self, mock_verify, db_session, setup_event_mocks):
        controller, mock_event_dao, _, _, _, mock_auth = setup_event_mocks
        mock_verify.return_value = {"sub": 99, "department": "gestion"}
        token = get_mock_gestion_token_str()
        mock_auth.check_permission.return_value = True
        mock_event_dao.delete.return_value = False

        result = controller.delete_event(token, db_session, 999)

        assert result is False
        mock_auth.check_permission.assert_called_with(token, "delete_event")
        mock_event_dao.delete.assert_called_once_with(db_session, 999)
