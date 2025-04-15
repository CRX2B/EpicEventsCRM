import pytest
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from epiceventsCRM.models.models import User, Department, Client, Contract, Event
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.event_dao import EventDAO
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.views.client_view import ClientView
from epiceventsCRM.views.event_view import EventView
from epiceventsCRM.utils.auth import generate_token
from epiceventsCRM.controllers.auth_controller import AuthController
from unittest.mock import Mock
from epiceventsCRM.tests.mocks.mock_controllers import MockAuthController
from epiceventsCRM.tests.mocks.mock_dao import MockClientDAO, MockContractDAO, MockEventDAO


class TestCompleteWorkflow:
    """Tests d'intégration complets du workflow de l'application"""

    def test_user_management(self, db_session, departments):
        """Test la gestion complète des utilisateurs"""
        # Création d'un utilisateur
        user_dao = UserDAO()
        user = user_dao.create(
            db_session,
            {
                "fullname": "Test User",
                "email": "test@example.com",
                "password": "password123",
                "departement_id": departments[1].id,  # ID du département support
            },
        )
        assert user.id is not None
        assert user.email == "test@example.com"

        # Test d'authentification
        authenticated_user = user_dao.authenticate(
            db_session, "test@example.com", "password123"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == user.id

        # Test de mise à jour du mot de passe
        updated_user = user_dao.update_password(
            db_session, user.id, "newpassword123"
        )
        assert updated_user is not None
        assert user_dao.authenticate(
            db_session, "test@example.com", "newpassword123"
        ) is not None

    def test_complete_client_workflow(self, db_session, departments):
        """Test le workflow complet de gestion client"""
        # Création d'un commercial
        user_dao = UserDAO()
        commercial = user_dao.create(
            db_session,
            {
                "fullname": "commercial_test",
                "email": "commercial@test.com",
                "password": "password123",
                "departement_id": departments[0].id,  # ID du département commercial
            },
        )

        # Création d'un client
        client_dao = ClientDAO()
        client = client_dao.create(
            db_session,
            {
                "fullname": "Client Test",
                "email": "client@test.com",
                "phone_number": 123456789,  # Utilisation d'un entier
                "enterprise": "Test Company",
                "sales_contact_id": commercial.id,
            },
        )

        # Vérification que le client a bien été créé avec le bon commercial
        assert client.id is not None
        assert client.sales_contact_id == commercial.id
        assert client.enterprise == "Test Company"

        # Mise à jour du client
        updated_client = client_dao.update(
            db_session,
            client,
            {
                "phone_number": 987654321,  # Utilisation d'un entier
                "enterprise": "Updated Company"
            }
        )
        assert updated_client.phone_number == 987654321
        assert updated_client.enterprise == "Updated Company"

        # Création d'un contrat
        contract_dao = ContractDAO()
        contract = contract_dao.create(
            db_session,
            {
                "client_id": client.id,
                "amount": 1000.00,
                "remaining_amount": 1000.00,
                "status": False,
                "sales_contact_id": commercial.id,
            },
        )

        # Vérification du contrat
        assert contract.id is not None
        assert contract.client_id == client.id
        assert contract.amount == 1000.00
        assert contract.remaining_amount == 1000.00
        assert contract.status is False

        # Mise à jour du contrat
        updated_contract = contract_dao.update(
            db_session,
            contract,
            {
                "status": True,
                "remaining_amount": 500.00
            }
        )
        assert updated_contract.status is True
        assert updated_contract.remaining_amount == 500.00

        # Création d'un événement
        event_dao = EventDAO()
        event = event_dao.create_event(
            db_session,
            {
                "contract_id": contract.id,
                "name": "Événement Test",
                "start_event": datetime(2024, 1, 1),
                "end_event": datetime(2024, 1, 2),
                "location": "Paris",
                "attendees": 50,
                "notes": "Notes de test",
            },
        )

        # Vérification de l'événement
        assert event.id is not None
        assert event.contract_id == contract.id
        assert event.location == "Paris"
        assert event.attendees == 50

        # Vérification de la chaîne complète
        retrieved_event = event_dao.get(db_session, event.id)
        assert retrieved_event.contract.client.id == client.id
        assert retrieved_event.contract.client.sales_contact.id == commercial.id
        assert retrieved_event.contract.status is True
        assert retrieved_event.contract.remaining_amount == 500.00

    def test_event_support_assignment(self, db_session, departments):
        """Test l'assignation d'un support à un événement"""
        # Création des utilisateurs
        user_dao = UserDAO()
        commercial = user_dao.create(
            db_session,
            {
                "fullname": "Commercial Test",
                "email": "commercial@test.com",
                "password": "password123",
                "departement_id": departments[0].id,  # ID du département commercial
            },
        )
        support = user_dao.create(
            db_session,
            {
                "fullname": "Support Test",
                "email": "support@test.com",
                "password": "password123",
                "departement_id": departments[1].id,  # ID du département support
            },
        )

        # Création d'un client et d'un contrat
        client_dao = ClientDAO()
        client = client_dao.create(
            db_session,
            {
                "fullname": "Client Test",
                "email": "client@test.com",
                "phone_number": 123456789,  # Utilisation d'un entier
                "enterprise": "Test Company",
                "sales_contact_id": commercial.id,
            },
        )

        contract_dao = ContractDAO()
        contract = contract_dao.create(
            db_session,
            {
                "client_id": client.id,
                "amount": 1000.00,
                "remaining_amount": 1000.00,
                "status": True,
                "sales_contact_id": commercial.id,
            },
        )

        # Création d'un événement sans support
        event_dao = EventDAO()
        event = event_dao.create_event(
            db_session,
            {
                "contract_id": contract.id,
                "name": "Événement Test",
                "start_event": datetime(2024, 1, 1),
                "end_event": datetime(2024, 1, 2),
                "location": "Paris",
                "attendees": 50,
                "notes": "Notes de test",
            },
        )
        assert event.support_contact_id is None

        # Assignation d'un support à l'événement
        updated_event = event_dao.assign_support_contact(
            db_session,
            event.id,
            support.id
        )
        assert updated_event.support_contact_id == support.id
        assert updated_event.support_contact.fullname == "Support Test"
        
        # Chargement des relations pour le support
        support_with_dept = db_session.query(User).options(
            joinedload(User.department)
        ).filter(User.id == support.id).first()
        assert support_with_dept.department.departement_name == "support"

    def test_client_search_and_filters(self, db_session, departments):
        """Test la recherche et le filtrage des clients"""
        # Création d'un commercial
        user_dao = UserDAO()
        commercial = user_dao.create(
            db_session,
            {
                "fullname": "commercial_test",
                "email": "commercial@test.com",
                "password": "password123",
                "departement_id": departments[0].id,
            },
        )

        # Création de plusieurs clients
        client_dao = ClientDAO()
        clients = []
        for i in range(3):
            client = client_dao.create(
                db_session,
                {
                    "fullname": f"Client Test {i}",
                    "email": f"client{i}@test.com",
                    "phone_number": 123456789 + i,
                    "enterprise": f"Company {i}",
                    "sales_contact_id": commercial.id,
                },
            )
            clients.append(client)

        # Test de recherche par email
        found_client = client_dao.get_by_email(db_session, "client1@test.com")
        assert found_client is not None
        assert found_client.email == "client1@test.com"

        # Test de recherche par entreprise
        found_clients = list(db_session.scalars(
            select(Client).where(Client.enterprise == "Company 2")
        ))
        assert len(found_clients) == 1
        assert found_clients[0].enterprise == "Company 2"

    def test_event_management(self, db_session, departments):
        """Test la gestion complète des événements"""
        # Création des utilisateurs
        user_dao = UserDAO()
        commercial = user_dao.create(
            db_session,
            {
                "fullname": "Commercial Test",
                "email": "commercial@test.com",
                "password": "password123",
                "departement_id": departments[0].id,
            },
        )
        support = user_dao.create(
            db_session,
            {
                "fullname": "Support Test",
                "email": "support@test.com",
                "password": "password123",
                "departement_id": departments[1].id,
            },
        )

        # Création d'un token pour le commercial
        token = generate_token(commercial.id, departments[0].departement_name)

        # Création d'un client et d'un contrat
        client_dao = ClientDAO()
        client = client_dao.create(
            db_session,
            {
                "fullname": "Client Test",
                "email": "client@test.com",
                "phone_number": 123456789,
                "enterprise": "Test Company",
                "sales_contact_id": commercial.id,
            },
        )

        contract_dao = ContractDAO()
        contract = contract_dao.create(
            db_session,
            {
                "client_id": client.id,
                "amount": 1000.00,
                "remaining_amount": 1000.00,
                "status": True,
                "sales_contact_id": commercial.id,
            },
        )

        # Création de plusieurs événements
        event_dao = EventDAO()
        events = []
        for i in range(3):
            event = event_dao.create_event(
                db_session,
                {
                    "contract_id": contract.id,
                    "name": f"Événement Test {i}",
                    "start_event": datetime(2024, 1, 1 + i),
                    "end_event": datetime(2024, 1, 2 + i),
                    "location": f"Location {i}",
                    "attendees": 50 + i,
                    "notes": f"Notes {i}",
                    "support_contact_id": support.id if i == 0 else None,
                },
            )
            events.append(event)

        # Test de recherche d'événements par contrat
        found_events = event_dao.get_by_contract(db_session, contract.id)
        assert len(found_events) == 3

        # Test de recherche d'événements par location
        found_events = list(db_session.scalars(
            select(Event).where(Event.location == "Location 1")
        ))
        assert len(found_events) == 1
        assert found_events[0].location == "Location 1"

        # Test de mise à jour d'événement
        updated_event = event_dao.update(
            db_session,
            events[0],
            {
                "location": "Nouvelle Location",
                "attendees": 100,
            },
        )
        assert updated_event.location == "Nouvelle Location"
        assert updated_event.attendees == 100

        # Test de suppression d'événement
        event_dao.delete(db_session, events[2].id)
        deleted_event = event_dao.get(db_session, events[2].id)
        assert deleted_event is None

    def test_client_controller_methods(self, db_session, departments):
        """Test les méthodes du contrôleur client"""
        # Création d'un commercial
        user_dao = UserDAO()
        commercial = user_dao.create(
            db_session,
            {
                "fullname": "commercial_test",
                "email": "commercial@test.com",
                "password": "password123",
                "departement_id": departments[0].id,  # Département commercial
            },
        )

        # Création d'un token pour le commercial avec les bonnes permissions
        token = generate_token(commercial.id, departments[0].departement_name)
        mock_auth = MockAuthController("commercial")
        mock_auth.users["commercial"]["permissions"] = ["create_client", "read_client", "update_client"]

        # Initialisation des DAOs
        client_dao = MockClientDAO()
        # Initialisation du contrôleur
        client_controller = ClientController()
        client_controller.auth_controller = mock_auth

        # Test de création de client
        client_data = {
            "fullname": "Client Test",
            "email": "client@test.com",
            "phone_number": 123456789,
            "enterprise": "Test Company",
            "sales_contact_id": commercial.id
        }
        client = client_controller.create(token, db_session, client_data)
        assert client is not None
        assert client.sales_contact_id == commercial.id

    def test_contract_controller_methods(self, db_session, departments):
        """Test les méthodes du contrôleur contrat"""
        # Création d'un commercial et d'un gestionnaire
        user_dao = UserDAO()
        commercial = user_dao.create(
            db_session,
            {
                "fullname": "commercial_test",
                "email": "commercial@test.com",
                "password": "password123",
                "departement_id": departments[0].id,  # Département commercial
            },
        )
        gestion = user_dao.create(
            db_session,
            {
                "fullname": "gestion_test",
                "email": "gestion@test.com",
                "password": "password123",
                "departement_id": departments[1].id,  # Département gestion
            },
        )

        # Création des tokens avec les bonnes permissions
        token_commercial = generate_token(commercial.id, departments[0].departement_name)
        token_gestion = generate_token(gestion.id, departments[1].departement_name)
        mock_auth = MockAuthController(department="gestion")

        # Création d'un client
        client_dao = MockClientDAO()
        client = client_dao.create(
            db_session,
            {
                "fullname": "Client Test",
                "email": "client@test.com",
                "phone_number": 123456789,
                "enterprise": "Test Company",
                "sales_contact_id": commercial.id,
            },
        )

        # Initialisation des DAOs
        contract_dao = MockContractDAO()
        # Initialisation du contrôleur
        contract_controller = ContractController()
        contract_controller.auth_controller = mock_auth
        contract_controller.dao = contract_dao
        contract_controller.client_dao = client_dao

        # Test de création d'un contrat
        contract_data = {
            "client_id": client.id,
            "amount": 1000.0,
            "remaining_amount": 1000.0,
            "status": False
        }
        contract = contract_controller.create(token_gestion, db_session, contract_data)
        assert contract is not None
        assert contract.client_id == client.id
        assert contract.amount == 1000.0

    def test_event_controller_methods(self, db_session, departments):
        """Test les méthodes du contrôleur événement"""
        # Création des utilisateurs
        user_dao = UserDAO()
        commercial = user_dao.create(
            db_session,
            {
                "fullname": "commercial_test",
                "email": "commercial@test.com",
                "password": "password123",
                "departement_id": departments[0].id,  # Département commercial
            },
        )
        support = user_dao.create(
            db_session,
            {
                "fullname": "support_test",
                "email": "support@test.com",
                "password": "password123",
                "departement_id": departments[2].id,  # Département support
            },
        )

        # Création des tokens avec les bonnes permissions
        token_commercial = generate_token(commercial.id, departments[0].departement_name)
        token_support = generate_token(support.id, departments[2].departement_name)
        mock_auth = MockAuthController(department="commercial")

        # Création d'un client et d'un contrat
        client_dao = MockClientDAO()
        client = client_dao.create(
            db_session,
            {
                "fullname": "Client Test",
                "email": "client@test.com",
                "phone_number": 123456789,
                "enterprise": "Test Company",
                "sales_contact_id": commercial.id,
            },
        )

        contract_dao = MockContractDAO()
        contract_data = {
            "client_id": client.id,
            "amount": 1000.00,
            "remaining_amount": 1000.00,
            "status": True,
            "sales_contact_id": commercial.id,
        }
        contract = contract_dao.create(db_session, contract_data)

        # Initialisation des DAOs
        event_dao = MockEventDAO()
        # Initialisation du contrôleur
        event_controller = EventController()
        event_controller.auth_controller = mock_auth
        event_controller.dao = event_dao
        event_controller.contract_dao = contract_dao

        # Test de création d'événement
        event_data = {
            "name": "Événement Test",
            "contract_id": contract.id,
            "start_event": datetime(2024, 1, 1),
            "end_event": datetime(2024, 1, 2),
            "location": "Paris",
            "attendees": 50,
            "notes": "Notes de test",
        }
        event = event_controller.create(token_commercial, db_session, event_data)
        assert event is not None
        assert event.contract_id == contract.id

        # Test de récupération d'événement
        retrieved_event = event_controller.get(token_commercial, db_session, event.id)
        assert retrieved_event is not None
        assert retrieved_event.name == "Événement Test"
        assert retrieved_event.contract_id == contract.id

        # Test de récupération des événements par contrat
        contract_events = event_controller.get_events_by_contract(
            token_commercial, db_session, contract.id
        )
        assert len(contract_events) == 1
        assert contract_events[0].id == event.id
