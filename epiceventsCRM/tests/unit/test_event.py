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
from epiceventsCRM.tests.mocks.mock_dao import MockEventDAO
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
