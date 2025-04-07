import pytest
from unittest.mock import MagicMock, patch
import click
from click.testing import CliRunner
from datetime import datetime, timedelta

from epiceventsCRM.models.models import Event, Contract, Client, User, Department
from epiceventsCRM.utils.auth import hash_password

@pytest.fixture
def test_data(db_session):
    """Créer les données de test dans la base de données."""
    # Départements
    commercial_dept = Department(departement_name="commercial")
    support_dept = Department(departement_name="support")
    
    db_session.add_all([commercial_dept, support_dept])
    db_session.commit()
    
    # Utilisateurs
    commercial_user = User(
        fullname="Commercial Test",
        email="commercial@test.com",
        password=hash_password("password"),
        departement_id=commercial_dept.id
    )
    
    support_user = User(
        fullname="Support Test",
        email="support@test.com",
        password=hash_password("password"),
        departement_id=support_dept.id
    )
    
    db_session.add_all([commercial_user, support_user])
    db_session.commit()
    
    # Client
    client = Client(
        fullname="Client Test",
        email="client@test.com",
        phone_number=123456789,
        enterprise="Enterprise Test",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=commercial_user.id
    )
    
    db_session.add(client)
    db_session.commit()
    
    # Contract
    contract = Contract(
        client_id=client.id,
        amount=1000.0,
        remaining_amount=1000.0,
        create_date=datetime.now(),
        status=False,
        sales_contact_id=commercial_user.id
    )
    
    db_session.add(contract)
    db_session.commit()
    
    # Event
    event = Event(
        name="Test Event",
        contract_id=contract.id,
        client_id=client.id,
        start_event=datetime.now(),
        end_event=datetime.now() + timedelta(hours=2),
        location="Test Location",
        support_contact_id=support_user.id,
        attendees=10,
        notes="Test Notes"
    )
    
    db_session.add(event)
    db_session.commit()
    
    return {
        "commercial_user": commercial_user,
        "support_user": support_user,
        "client": client,
        "contract": contract,
        "event": event,
        "commercial_dept": commercial_dept,
        "support_dept": support_dept
    }

def test_event_model(db_session, test_data):
    """Test simple pour vérifier que le modèle Event fonctionne correctement."""
    # Récupérer l'événement créé dans le fixture
    from epiceventsCRM.dao.event_dao import EventDAO
    event_dao = EventDAO()
    event = event_dao.get(db_session, test_data["event"].id)
    
    # Vérifications
    assert event is not None
    assert event.name == "Test Event"
    assert event.contract_id == test_data["contract"].id
    assert event.client_id == test_data["client"].id
    assert event.location == "Test Location"
    assert event.support_contact_id == test_data["support_user"].id
    assert event.attendees == 10
    assert event.notes == "Test Notes"
    
    # Vérifier la relation avec le contrat
    assert event.contract is not None
    assert event.contract.id == test_data["contract"].id
    
    # Vérifier la relation avec le client
    assert event.client is not None
    assert event.client.id == test_data["client"].id
    
    # Vérifier la relation avec le contact support
    assert event.support_contact is not None
    assert event.support_contact.id == test_data["support_user"].id

def test_event_permissions(db_session, test_data):
    """Test des permissions d'accès sur les événements."""
    from epiceventsCRM.utils.permissions import has_permission
    
    # Vérifier les permissions des différents départements
    commercial_dept = test_data["commercial_dept"].departement_name
    support_dept = test_data["support_dept"].departement_name
    
    # Le commercial peut créer des événements
    assert has_permission(commercial_dept, "create_event") is True
    
    # Le support ne peut pas créer des événements
    assert has_permission(support_dept, "create_event") is False
    
    # Le commercial ne peut pas mettre à jour un événement
    assert has_permission(commercial_dept, "update_event") is False
    
    # Le support peut mettre à jour un événement
    assert has_permission(support_dept, "update_event") is True
    
    # Les deux peuvent lire des événements
    assert has_permission(commercial_dept, "read_event") is True
    assert has_permission(support_dept, "read_event") is True 