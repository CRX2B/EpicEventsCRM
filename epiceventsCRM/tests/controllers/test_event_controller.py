import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.models.models import Event, Contract, Client, User, Department
from epiceventsCRM.utils.auth import hash_password

@pytest.fixture
def test_data(db_session):
    """Créer les données de test dans la base de données."""
    # Départements
    commercial_dept = Department(departement_name="commercial")
    gestion_dept = Department(departement_name="gestion")
    support_dept = Department(departement_name="support")
    
    db_session.add_all([commercial_dept, gestion_dept, support_dept])
    db_session.commit()
    
    # Utilisateurs
    commercial_user = User(
        fullname="Commercial Test",
        email="commercial@test.com",
        password=hash_password("password"),
        departement_id=commercial_dept.id
    )
    
    gestion_user = User(
        fullname="Gestion Test",
        email="gestion@test.com",
        password=hash_password("password"),
        departement_id=gestion_dept.id
    )
    
    support_user = User(
        fullname="Support Test",
        email="support@test.com",
        password=hash_password("password"),
        departement_id=support_dept.id
    )
    
    db_session.add_all([commercial_user, gestion_user, support_user])
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
    
    return {
        "commercial_user": commercial_user,
        "gestion_user": gestion_user,
        "support_user": support_user,
        "client": client,
        "contract": contract,
        "commercial_dept": commercial_dept,
        "gestion_dept": gestion_dept,
        "support_dept": support_dept
    }

def test_event_crud_simple(db_session, test_data):
    """Test simplifié des fonctionnalités CRUD pour un événement."""
    # Créer un événement directement dans la base de données
    event = Event(
        name="Test Event",
        contract_id=test_data["contract"].id,
        client_id=test_data["client"].id,
        start_event=datetime.now(),
        end_event=datetime.now() + timedelta(hours=2),
        location="Test Location",
        support_contact_id=test_data["support_user"].id,
        attendees=10,
        notes="Test Notes"
    )
    
    db_session.add(event)
    db_session.commit()
    
    # Récupérer l'événement via le DAO
    from epiceventsCRM.dao.event_dao import EventDAO
    event_dao = EventDAO()
    retrieved_event = event_dao.get(db_session, event.id)
    
    # Vérifications
    assert retrieved_event is not None
    assert retrieved_event.id == event.id
    assert retrieved_event.name == "Test Event"
    
    # Test de mise à jour
    event.name = "Updated Event"
    event.notes = "Updated Notes"
    db_session.commit()
    
    updated_event = event_dao.get(db_session, event.id)
    assert updated_event.name == "Updated Event"
    assert updated_event.notes == "Updated Notes"
    
    # Test de suppression
    db_session.delete(event)
    db_session.commit()
    
    deleted_event = event_dao.get(db_session, event.id)
    assert deleted_event is None

def test_event_departments_access(db_session, test_data):
    """Test des permissions par département sur les événements."""
    # Créer un événement
    event = Event(
        name="Permission Test Event",
        contract_id=test_data["contract"].id,
        client_id=test_data["client"].id,
        start_event=datetime.now(),
        end_event=datetime.now() + timedelta(hours=2),
        location="Permission Test Location",
        support_contact_id=test_data["support_user"].id,
        attendees=15,
        notes="Permission Test Notes"
    )
    
    db_session.add(event)
    db_session.commit()
    
    # Test des permissions selon les départements
    # Note: Nous n'utilisons pas d'authentication réelle ici
    # puisque nous testons simplement que les départements ont les bonnes permissions
    
    # 1. Le commercial peut créer des événements
    from epiceventsCRM.utils.permissions import has_permission
    assert has_permission(test_data["commercial_dept"].departement_name, "create_event") is True
    
    # 2. Le support ne peut pas créer des événements
    assert has_permission(test_data["support_dept"].departement_name, "create_event") is False
    
    # 3. Le commercial ne peut pas mettre à jour des événements
    assert has_permission(test_data["commercial_dept"].departement_name, "update_event") is False
    
    # 4. Le support peut mettre à jour des événements
    assert has_permission(test_data["support_dept"].departement_name, "update_event") is True
    
    # 5. Tous les départements peuvent lire des événements
    assert has_permission(test_data["commercial_dept"].departement_name, "read_event") is True
    assert has_permission(test_data["support_dept"].departement_name, "read_event") is True
    assert has_permission(test_data["gestion_dept"].departement_name, "read_event") is True 