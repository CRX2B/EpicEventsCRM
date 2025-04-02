import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from epiceventsCRM.dao.event_dao import EventDAO
from epiceventsCRM.models.models import Event, Contract, Client, User, Department


class TestEventDAO:
    """Tests pour la classe EventDAO"""

    def test_create_event(self, db_session: Session):
        """Test de création d'un événement"""
        # Créer les données de test nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        support_contact = User(
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()

        # Créer l'événement avec EventDAO
        event_dao = EventDAO(db_session)
        event = event_dao.create_event(
            name="Test Event",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Test Location",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Test Notes"
        )

        # Vérifier l'événement créé
        assert event is not None
        assert event.name == "Test Event"
        assert event.contract_id == contract.id
        assert event.client_id == client.id
        assert event.location == "Test Location"
        assert event.support_contact_id == support_contact.id
        assert event.attendees == 10
        assert event.notes == "Test Notes"

    def test_get_event_by_id(self, db_session: Session):
        """Test de récupération d'un événement par ID"""
        # Créer un événement de test
        event_dao = EventDAO(db_session)
        
        # Créer les données nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        support_contact = User(
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()

        # Créer un événement
        event = event_dao.create_event(
            name="Test Event",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Test Location",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Test Notes"
        )
        
        # Récupérer l'événement par ID
        retrieved_event = event_dao.get_event_by_id(event.id)
        
        # Vérifier l'événement récupéré
        assert retrieved_event is not None
        assert retrieved_event.id == event.id
        assert retrieved_event.name == "Test Event"
        assert retrieved_event.contract_id == contract.id
        assert retrieved_event.client_id == client.id
        
        # Test avec un ID inexistant
        non_existent_event = event_dao.get_event_by_id(9999)
        assert non_existent_event is None

    def test_get_all_events(self, db_session: Session):
        """Test de récupération de tous les événements"""
        # Récupérer le nombre d'événements existants
        event_dao = EventDAO(db_session)
        initial_count = len(event_dao.get_all_events())
        
        # Créer les données nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        support_contact = User(
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()
            
        # Créer deux nouveaux événements
        event_dao.create_event(
            name="Event 1",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Location 1",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Notes 1"
        )
        
        event_dao.create_event(
            name="Event 2",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Location 2",
            support_contact_id=support_contact.id,
            attendees=20,
            notes="Notes 2"
        )
        
        # Récupérer tous les événements
        events = event_dao.get_all_events()
        
        # Vérifier qu'il y a deux événements de plus
        assert len(events) == initial_count + 2

    def test_get_events_by_client(self, db_session: Session):
        """Test de récupération des événements par client"""
        event_dao = EventDAO(db_session)
        
        # Créer les données nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        # Créer un nouveau client pour ce test
        client = Client(
            fullname="Client Test 2",
            email="client2@test.com",
            phone_number=987654321,
            enterprise="Enterprise Test 2",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        support_contact = User(
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()
        
        # Créer deux événements pour ce client
        event_dao.create_event(
            name="Event 1",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Location 1",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Notes 1"
        )
        
        event_dao.create_event(
            name="Event 2",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Location 2",
            support_contact_id=support_contact.id,
            attendees=20,
            notes="Notes 2"
        )
        
        # Récupérer les événements par client
        client_events = event_dao.get_events_by_client(client.id)
        
        # Vérifier qu'il y a deux événements pour ce client
        assert len(client_events) == 2
        assert all(event.client_id == client.id for event in client_events)

    def test_get_events_by_contract(self, db_session: Session):
        """Test de récupération des événements par contrat"""
        event_dao = EventDAO(db_session)
        
        # Créer les données nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        # Créer un nouveau contrat pour ce test
        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        support_contact = User(
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()
        
        # Créer deux événements pour ce contrat
        event_dao.create_event(
            name="Event 1",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Location 1",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Notes 1"
        )
        
        event_dao.create_event(
            name="Event 2",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Location 2",
            support_contact_id=support_contact.id,
            attendees=20,
            notes="Notes 2"
        )
        
        # Récupérer les événements par contrat
        contract_events = event_dao.get_events_by_contract(contract.id)
        
        # Vérifier qu'il y a deux événements pour ce contrat
        assert len(contract_events) == 2
        assert all(event.contract_id == contract.id for event in contract_events)

    def test_get_events_by_support_contact(self, db_session: Session):
        """Test de récupération des événements par contact support"""
        event_dao = EventDAO(db_session)
        
        # Créer les données nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        # Créer un nouveau contact support pour ce test
        support_contact = User(
            fullname="Support Test 2",
            email="support2@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()
        
        # Créer deux événements pour ce contact support
        event_dao.create_event(
            name="Event 1",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Location 1",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Notes 1"
        )
        
        event_dao.create_event(
            name="Event 2",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Location 2",
            support_contact_id=support_contact.id,
            attendees=20,
            notes="Notes 2"
        )
        
        # Récupérer les événements par contact support
        support_events = event_dao.get_events_by_support_contact(support_contact.id)
        
        # Vérifier qu'il y a deux événements pour ce contact support
        assert len(support_events) == 2
        assert all(event.support_contact_id == support_contact.id for event in support_events)

    def test_update_event(self, db_session: Session):
        """Test de mise à jour d'un événement"""
        event_dao = EventDAO(db_session)
        
        # Créer les données nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        support_contact = User(
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()

        # Créer un événement
        event = event_dao.create_event(
            name="Test Event",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Test Location",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Test Notes"
        )
        
        # Mettre à jour l'événement
        update_data = {
            "name": "Updated Event",
            "location": "Updated Location",
            "attendees": 20,
            "notes": "Updated Notes"
        }
        
        updated_event = event_dao.update_event(event.id, update_data)
        
        # Vérifier les modifications
        assert updated_event.name == "Updated Event"
        assert updated_event.location == "Updated Location"
        assert updated_event.attendees == 20
        assert updated_event.notes == "Updated Notes"

    def test_assign_support_contact(self, db_session: Session):
        """Test d'assignation d'un contact support"""
        event_dao = EventDAO(db_session)
        
        # Créer les données nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        support_contact = User(
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()

        # Créer un événement
        event = event_dao.create_event(
            name="Test Event",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Test Location",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Test Notes"
        )
        
        # Créer un nouveau contact support
        new_support_contact = User(
            fullname="New Support Test",
            email="new_support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(new_support_contact)
        db_session.flush()
        
        # Assigner le nouveau contact support
        updated_event = event_dao.assign_support_contact(event.id, new_support_contact.id)
        
        # Vérifier l'assignation
        assert updated_event.support_contact_id == new_support_contact.id

    def test_delete_event(self, db_session: Session):
        """Test de suppression d'un événement"""
        event_dao = EventDAO(db_session)
        
        # Créer les données nécessaires
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        contract = Contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=True
        )
        db_session.add(contract)
        db_session.flush()

        support_contact = User(
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(support_contact)
        db_session.flush()

        # Créer un événement
        event = event_dao.create_event(
            name="Test Event",
            contract_id=contract.id,
            client_id=client.id,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Test Location",
            support_contact_id=support_contact.id,
            attendees=10,
            notes="Test Notes"
        )
        
        # Supprimer l'événement
        result = event_dao.delete_event(event.id)
        
        # Vérifier la suppression
        assert result is True
        deleted_event = event_dao.get_event_by_id(event.id)
        assert deleted_event is None 