import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epiceventsCRM.models.models import Base, User, Department
from epiceventsCRM.config import DATABASE_URL
from epiceventsCRM.database import get_db

# Création d'une base de données de test
TEST_DATABASE_URL = DATABASE_URL + "_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    """Crée le moteur de base de données de test."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Crée une nouvelle session de base de données pour chaque test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_department(db_session):
    """Crée un département de test."""
    department = Department(departement_name="commercial")
    db_session.add(department)
    db_session.commit()
    return department

@pytest.fixture(scope="function")
def test_user(db_session, test_department):
    """Crée un utilisateur de test."""
    user = User(
        fullname="Test User",
        email="test@example.com",
        password="hashed_password",  # Le hashage sera testé séparément
        departement_id=test_department.id
    )
    db_session.add(user)
    db_session.commit()
    return user 