import os
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from click.testing import CliRunner

from epiceventsCRM.config import DATABASE_URL
from epiceventsCRM.models.models import Base, Department, User, Client, Contract, Event
from epiceventsCRM.utils.auth import hash_password


@pytest.fixture(scope="session")
def engine():
    """Crée une instance de moteur SQLAlchemy pour les tests."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="session")
def tables(engine):
    """Crée toutes les tables dans la base de données de test."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Crée une nouvelle session de base de données pour chaque test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def departments(db_session):
    """Crée les départements de test."""
    departments = []
    names = ["commercial", "support", "gestion"]

    for name in names:
        dept = Department(departement_name=name)
        db_session.add(dept)
        departments.append(dept)

    db_session.commit()
    return departments


@pytest.fixture(scope="function")
def users(db_session, departments):
    """Crée plusieurs utilisateurs de test pour différents départements."""
    users = []

    commercial_user = User(
        fullname="Commercial User",
        email="commercial@example.com",
        password=hash_password("password123"),
        departement_id=departments[0].id,
    )
    db_session.add(commercial_user)
    users.append(commercial_user)

    support_user = User(
        fullname="Support User",
        email="support@example.com",
        password=hash_password("password123"),
        departement_id=departments[1].id,
    )
    db_session.add(support_user)
    users.append(support_user)

    management_user = User(
        fullname="Management User",
        email="management@example.com",
        password=hash_password("password123"),
        departement_id=departments[2].id,
    )
    db_session.add(management_user)
    users.append(management_user)

    db_session.commit()
    return users


@pytest.fixture(scope="function")
def clients(db_session, users):
    """Crée des clients de test associés à un commercial."""
    clients = []

    for i in range(3):
        client = Client(
            fullname=f"Client {i+1}",
            email=f"client{i+1}@example.com",
            phone_number=1234567890 + i,
            enterprise=f"Enterprise {i+1}",
            create_date=datetime.now(),
            sales_contact_id=users[0].id,
        )
        db_session.add(client)
        clients.append(client)

    db_session.commit()
    return clients


@pytest.fixture(scope="function")
def contracts(db_session, clients, users):
    """Crée des contrats de test associés aux clients."""
    contracts = []

    for i, client in enumerate(clients):
        contract = Contract(
            client_id=client.id,
            amount=1000.0 * (i + 1),
            remaining_amount=500.0 * (i + 1),
            create_date=datetime.now(),
            status=i % 2 == 0,
            sales_contact_id=users[0].id,
        )
        db_session.add(contract)
        contracts.append(contract)

    db_session.commit()
    return contracts


@pytest.fixture(scope="function")
def events(db_session, contracts, clients, users):
    """Crée des événements de test associés aux contrats."""
    events = []

    for i, contract in enumerate(contracts):
        event = Event(
            name=f"Event {i+1}",
            contract_id=contract.id,
            client_id=clients[i].id,
            client_name=clients[i].fullname,
            client_contact=clients[i].email,
            start_event=datetime.now() + timedelta(days=10),
            end_event=datetime.now() + timedelta(days=10, hours=8),
            location=f"Location {i+1}",
            support_contact_id=(users[1].id if i > 0 else None),
            attendees=100 * (i + 1),
            notes=f"Notes for event {i+1}",
        )
        db_session.add(event)
        events.append(event)

    db_session.commit()
    return events


@pytest.fixture
def mock_token_commercial():
    """Token simulé pour un utilisateur commercial."""
    return {"user_id": 1, "departement_id": 1}


@pytest.fixture
def mock_token_support():
    """Token simulé pour un utilisateur support."""
    return {"user_id": 2, "departement_id": 2}


@pytest.fixture
def mock_token_gestion():
    """Token simulé pour un utilisateur de gestion."""
    return {"user_id": 3, "departement_id": 2, "department": "gestion"}


@pytest.fixture
def cli_runner():
    """Fixture pour le CliRunner de Click."""
    return CliRunner()


@pytest.fixture
def mock_session():
    """Crée une session mock pour les tests CLI."""
    return type("MockSession", (), {})()


@pytest.fixture
def get_session_mock(mock_session):
    """Fonction qui renvoie une session mock pour les tests CLI."""
    return lambda: mock_session


@pytest.fixture
def get_token_mock(mock_token_management):
    """Fonction qui renvoie un token mock pour les tests CLI."""
    return lambda: mock_token_management


@pytest.fixture
def app_context(get_session_mock, get_token_mock):
    """Contexte d'application pour les tests CLI."""
    return {"session": get_session_mock(), "token": get_token_mock()}


@pytest.fixture
def setup_view_mocks(monkeypatch):
    """Configure les mocks pour toutes les vues."""

    def _setup_mocks(view_module):
        monkeypatch.setattr(
            f"epiceventsCRM.views.{view_module}.get_token",
            lambda: {"user_id": 3, "departement_id": 3},
        )
        return monkeypatch

    return _setup_mocks


@pytest.fixture
def test_department(db_session):
    """Fixture pour créer un département de test"""
    department = Department(departement_name="commercial")
    db_session.add(department)
    db_session.commit()
    return department


@pytest.fixture
def test_contract(db_session, test_client, test_commercial):
    """Fixture pour créer un contrat de test"""
    contract = Contract(
        client_id=test_client.id,
        amount=1000.0,
        remaining_amount=500.0,
        status=True,
        sales_contact_id=test_commercial.id,
    )
    db_session.add(contract)
    db_session.commit()
    return contract
