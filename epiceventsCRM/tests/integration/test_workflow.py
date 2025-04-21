import pytest
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import select

from epiceventsCRM.models.models import User, Department, Client, Contract, Event

from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.event_dao import EventDAO

from epiceventsCRM.utils.auth import hash_password, generate_token, verify_token


class TestPureIntegrationWorkflow:
    """Tests d'intégration purs utilisant la base de données réelle et les DAOs réels."""

    @pytest.fixture(autouse=True)
    def setup_daos(self):
        """Initialise les instances de DAO pour les tests de cette classe."""
        self.user_dao = UserDAO()
        self.client_dao = ClientDAO()
        self.contract_dao = ContractDAO()
        self.event_dao = EventDAO()

    def test_user_management(self, db_session, departments):
        """Test la création, authentification et mise à jour de mot de passe utilisateur."""
        test_email = "test_integ_user@example.com"

        user_data = {
            "fullname": "Test Integ User",
            "email": test_email,
            "password": "password123",
            "departement_id": departments[1].id,
        }
        user = self.user_dao.create(db_session, user_data)
        assert user is not None
        assert user.id is not None
        assert user.email == test_email
        assert user.password != "password123"

        authenticated_user = self.user_dao.authenticate(db_session, test_email, "password123")
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.email == test_email

        failed_auth_user = self.user_dao.authenticate(db_session, test_email, "wrongpassword")
        assert failed_auth_user is None

        updated_user = self.user_dao.update_password(db_session, user.id, "newpassword123")
        assert updated_user is not None
        new_auth_user = self.user_dao.authenticate(db_session, test_email, "newpassword123")
        assert new_auth_user is not None
        assert new_auth_user.id == user.id
        old_auth_user = self.user_dao.authenticate(db_session, test_email, "password123")
        assert old_auth_user is None

    def test_complete_sales_workflow(self, db_session, departments):
        """Test le workflow complet: commercial -> client -> contrat -> événement."""
        commercial_email = "integ_commercial@example.com"
        commercial = self.user_dao.create(
            db_session,
            {
                "fullname": "Integ Commercial",
                "email": commercial_email,
                "password": "commpassword",
                "departement_id": departments[0].id,
            },
        )
        assert commercial is not None

        client_email = "integ_client@example.com"
        client = self.client_dao.create_client(
            db_session,
            {
                "fullname": "Integ Client",
                "email": client_email,
                "phone_number": "111222333",
                "enterprise": "Integ Company",
                "sales_contact_id": commercial.id,
            },
        )
        assert client is not None
        assert client.sales_contact_id == commercial.id
        assert client.create_date is not None

        retrieved_client = self.client_dao.get(db_session, client.id)
        assert retrieved_client is not None
        assert retrieved_client.email == client_email
        assert retrieved_client.sales_contact.id == commercial.id

        updated_client = self.client_dao.update(
            db_session,
            client,
            {"enterprise": "Integ Company Updated"},
        )
        assert updated_client is not None
        assert updated_client.enterprise == "Integ Company Updated"

        contract = self.contract_dao.create_contract(
            db_session,
            client_id=client.id,
            amount=5000.00,
            sales_contact_id=commercial.id,
            status=False,
        )
        assert contract is not None
        assert contract.client_id == client.id
        assert contract.sales_contact_id == commercial.id
        assert not contract.status

        updated_contract = self.contract_dao.update(
            db_session,
            contract,
            {"status": True, "remaining_amount": 4500.00},
        )
        assert updated_contract is not None
        assert updated_contract.status is True
        assert updated_contract.remaining_amount == 4500.00

        event = self.event_dao.create_event(
            db_session,
            {
                "contract_id": contract.id,
                "name": "Grand Lancement Integ",
                "start_event": datetime(2025, 10, 20, 18, 00),
                "end_event": datetime(2025, 10, 20, 23, 00),
                "location": "Palais Brongniart",
                "attendees": 250,
                "notes": "Champagne et petits fours.",
            },
        )
        assert event is not None
        assert event.contract_id == contract.id
        assert event.attendees == 250
        assert event.support_contact_id is None

        retrieved_event = self.event_dao.get(db_session, event.id)
        assert retrieved_event is not None
        assert retrieved_event.contract.id == contract.id
        assert retrieved_event.contract.client.id == client.id
        assert retrieved_event.contract.sales_contact.id == commercial.id

    def test_event_support_assignment_workflow(self, db_session, departments):
        """Test la création d'un événement et l'assignation d'un support."""
        commercial = self.user_dao.create(
            db_session,
            {
                "fullname": "Assign Commercial",
                "email": "assign_comm@example.com",
                "password": "pass",
                "departement_id": departments[0].id,
            },
        )
        support_user = self.user_dao.create(
            db_session,
            {
                "fullname": "Assign Support",
                "email": "assign_supp@example.com",
                "password": "pass",
                "departement_id": departments[2].id,
            },
        )
        client = self.client_dao.create_client(
            db_session,
            {
                "fullname": "Assign Client",
                "email": "assign_cli@example.com",
                "phone_number": "444555666",
                "enterprise": "Assign Inc.",
                "sales_contact_id": commercial.id,
            },
        )
        contract = self.contract_dao.create_contract(
            db=db_session,
            client_id=client.id,
            amount=100.0,
            sales_contact_id=commercial.id,
            status=True,
        )

        event = self.event_dao.create_event(
            db_session,
            {
                "contract_id": contract.id,
                "name": "Événement à Assigner",
                "start_event": datetime(2025, 11, 1),
                "end_event": datetime(2025, 11, 2),
                "location": "Lieu d'assignation",
                "attendees": 10,
            },
        )
        assert event is not None
        assert event.support_contact_id is None

        updated_event = self.event_dao.update_support(db_session, event.id, support_user.id)

        db_session.refresh(updated_event)
        event_with_support = (
            db_session.query(Event)
            .options(joinedload(Event.support_contact))
            .filter(Event.id == event.id)
            .one()
        )

        assert event_with_support is not None
        assert event_with_support.support_contact_id == support_user.id
        assert event_with_support.support_contact is not None
        assert event_with_support.support_contact.fullname == "Assign Support"
        assert event_with_support.support_contact.departement_id == departments[2].id

        notes_added_event = self.event_dao.update(
            db_session,
            event_with_support,
            {"notes": "Support contacté, prêt pour l'événement."},
        )
        assert notes_added_event is not None
        assert notes_added_event.notes == "Support contacté, prêt pour l'événement."
