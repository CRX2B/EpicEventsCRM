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


@pytest.fixture
def test_support(db_session):
    """Fixture pour créer un support de test"""
    department = Department(departement_name="support")
    db_session.add(department)
    db_session.commit()

    user = User(
        fullname="Support Test",
        email="support@test.com",
        password="password123",
        departement_id=department.id,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_client(db_session):
    """Fixture pour créer un client de test"""
    client = Client(
        fullname="Test Client",
        email="client@test.com",
        phone_number=1234567890,
        enterprise="Test Company",
    )
    db_session.add(client)
    db_session.commit()
    return client


@pytest.fixture
def test_contract(db_session, test_client):
    """Fixture pour créer un contrat de test"""
    contract = Contract(
        client_id=test_client.id, amount=1000.00, remaining_amount=1000.00, status=False
    )
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def test_event_data(test_client, test_support, test_contract):
    """Fixture pour les données de test d'événement"""
    return {
        "name": "Test Event",
        "location": "Test Location",
        "contract_id": test_contract.id,
        "start_event": datetime.now(),
        "end_event": datetime.now() + timedelta(hours=2),
        "attendees": 50,
        "notes": "Test notes",
    }


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
        # Créer un événement
        event = event_dao.create_event(db_session, test_event_data)

        # Récupérer l'événement par ID
        retrieved_event = event_dao.get(db_session, event.id)
        assert retrieved_event is not None
        assert retrieved_event.location == event.location

        # Tester avec un ID inexistant
        event = event_dao.get(db_session, 9999)
        assert event is None

    def test_get_all(self, event_dao, db_session, test_event_data):
        """Test de récupération de tous les événements."""
        # Créer quelques événements
        event1 = event_dao.create_event(db_session, test_event_data)

        event_data2 = test_event_data.copy()
        event_data2["location"] = "Another Location"
        event_data2["notes"] = "Different notes"
        event2 = event_dao.create_event(db_session, event_data2)

        # Récupérer tous les événements
        all_events, total = event_dao.get_all(db_session)
        assert len(all_events) >= 2

        # Tester la pagination
        page1, total = event_dao.get_all(db_session, page=1, page_size=2)
        assert len(page1) <= 2

        # Nettoyage
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

        # Créer l'événement
        event = event_dao.create_event(db_session, event_data)
        assert event is not None
        assert event.contract_id == test_contract.id
        assert event.name == "Test Event"
        assert event.location == "Test Location Create"
        assert event.attendees == 75

    def test_update(self, event_dao, db_session, test_event_data):
        """Test de mise à jour d'un événement."""
        # Créer un événement
        event = event_dao.create_event(db_session, test_event_data)

        # Données de mise à jour
        update_data = {"location": "Updated Location", "attendees": 100}

        # Mettre à jour l'événement
        updated_event = event_dao.update(db_session, event, update_data)

        # Vérifier que l'événement a été mis à jour
        assert updated_event is not None
        assert updated_event.id == event.id
        assert updated_event.location == "Updated Location"
        assert updated_event.attendees == 100

    def test_delete(self, event_dao, db_session, test_event_data):
        """Test de suppression d'un événement."""
        # Créer un événement
        event = event_dao.create_event(db_session, test_event_data)

        # Vérifier que l'événement existe avant la suppression
        assert event_dao.get(db_session, event.id) is not None

        # Supprimer l'événement
        result = event_dao.delete(db_session, event.id)

        # Vérifier que la suppression a réussi
        assert result is True

        # Vérifier que l'événement n'existe plus
        assert event_dao.get(db_session, event.id) is None

    def test_get_by_contract(self, event_dao, db_session, test_contract, test_event_data):
        """Test de récupération des événements par contrat."""
        # Créer un événement pour le contrat
        event = event_dao.create_event(db_session, test_event_data)

        # Récupérer les événements du contrat
        contract_events = event_dao.get_by_contract(db_session, test_contract.id)

        # Vérifier que les événements sont liés au contrat
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

    # Pré-peupler les mocks si nécessaire
    mock_contract_dao._data[test_contract.id] = test_contract
    mock_user_dao._data[test_support.id] = test_support

    # Créer une instance du contrôleur avec les mocks
    event_controller = EventController()
    event_controller.dao = mock_event_dao
    event_controller.contract_dao = mock_contract_dao
    event_controller.user_dao = mock_user_dao
    event_controller.auth_controller = mock_auth_controller

    # Cloner les données pour éviter les modifications accidentelles
    initial_event_data = test_event_data.copy()
    initial_event_data["support_contact_id"] = test_support.id  # Assigner le support
    mock_event = mock_event_dao._create_impl(
        None, initial_event_data
    )  # Utilise _create_impl pour peupler sans appeler le mock public
    mock_event.id = 1  # Donner un ID fixe pour les tests
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
        mock_auth.check_permission.return_value = True  # Simuler permission OK

        # S'assurer que le contrat est marqué comme signé pour ce test
        contract = controller.contract_dao.get(db_session, test_event_data["contract_id"])
        contract.status = True

        event_data = test_event_data.copy()
        created_event = controller.create(token, db_session, event_data)

        # Vérifier que l'événement a été créé
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
        mock_auth.check_permission.return_value = (
            True  # Simuler permission OK pour atteindre le code de la méthode
        )

        # S'assurer que le contrat est marqué comme signé
        contract = controller.contract_dao.get(db_session, test_event_data["contract_id"])
        contract.status = True

        event_data_missing = test_event_data.copy()
        del event_data_missing["location"]

        # Vérifier que ValueError est levé
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
        # Utiliser le contrôleur et les autres mocks de la fixture, mais créer un mock DAO contrat spécifique
        controller, dao, _, _, _, mock_auth = setup_event_mocks
        mock_auth.check_permission.return_value = True

        # Créer un mock DAO contrat vierge pour ce test
        mock_contract_dao_specific = MockContractDAO()
        mock_contract_dao_specific.get.return_value = None  # Configurer pour retourner None
        # Assigner ce mock spécifique au contrôleur pour ce test
        controller.contract_dao = mock_contract_dao_specific

        event_data = test_event_data.copy()
        with pytest.raises(ValueError) as excinfo:
            controller.create(token, db_session, event_data)

        expected_error = f"Contrat avec ID {event_data['contract_id']} non trouvé"
        assert str(excinfo.value) == expected_error
        mock_auth.check_permission.assert_called_with(token, "create_event")
        # Vérifier que le mock DAO spécifique a bien été appelé
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

        # S'assurer que le contrat existe mais n'est PAS signé
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
        mock_auth.check_permission.return_value = True  # Simuler permission OK

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
        mock_auth.check_permission.return_value = (
            True  # Simuler permission OK pour atteindre le code
        )

        # La méthode retourne une liste vide si le token est invalide dans la logique actuelle
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
        mock_auth.check_permission.return_value = True  # Simuler permission OK
        event_id = mock_event.id
        # Assigner le bon support ID à l'événement mocké
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
        mock_auth.check_permission.return_value = True  # Simuler permission OK
        event_id = mock_event.id
        # Assigner un ID de support différent à l'événement mocké
        mock_event.support_contact_id = 123
        new_notes = "Tentative de notes."

        dao.get.return_value = mock_event

        # Vérifier que PermissionError est levée
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
        mock_auth.check_permission.return_value = True  # Simuler permission OK
        event_id = 999
        new_notes = "Notes pour rien."

        dao.get.return_value = None

        # La méthode retourne None si l'événement n'est pas trouvé
        result = controller.update_event_notes(token, db_session, event_id, new_notes)

        assert result is None
        mock_auth.check_permission.assert_called_with(token, "update_event")
        dao.get.assert_called_once_with(db_session, event_id)
        dao.update_notes.assert_not_called()
