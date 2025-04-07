import pytest
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.models.models import User, Department, Client
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.utils.auth import hash_password
from datetime import datetime
from time import sleep

@pytest.fixture
def user_commercial(db_session):
    """Fixture pour créer un utilisateur commercial."""
    # Création du département commercial
    commercial_dept = Department(departement_name="commercial")
    db_session.add(commercial_dept)
    db_session.commit()
    
    # Création de l'utilisateur commercial
    user_data = {
        "fullname": "Commercial User",
        "email": "commercial@test.com",
        "password": hash_password("password123"),
        "departement_id": commercial_dept.id
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    
    return user

@pytest.fixture
def user_support(db_session):
    """Fixture pour créer un utilisateur support."""
    # Création du département support
    support_dept = Department(departement_name="support")
    db_session.add(support_dept)
    db_session.commit()
    
    # Création de l'utilisateur support
    user_data = {
        "fullname": "Support User",
        "email": "support@test.com",
        "password": hash_password("password123"),
        "departement_id": support_dept.id
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    
    return user

@pytest.fixture
def test_client(db_session, user_commercial):
    """Fixture pour créer un client de test."""
    client = Client(
        fullname="Test Client",
        email="client@test.com",
        phone_number=123456789,
        enterprise="Test Enterprise",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=user_commercial.id
    )
    db_session.add(client)
    db_session.commit()
    
    return client

@pytest.fixture
def auth_token_commercial(db_session, user_commercial):
    """Fixture pour générer un token JWT pour un utilisateur commercial."""
    auth_controller = AuthController()
    token = auth_controller.login(db_session, user_commercial.email, "password123")
    return token["token"]

@pytest.fixture
def auth_token_support(db_session, user_support):
    """Fixture pour générer un token JWT pour un utilisateur support."""
    auth_controller = AuthController()
    token = auth_controller.login(db_session, user_support.email, "password123")
    return token["token"]

def test_client_crud_operations(db_session, auth_token_commercial):
    """Test fonctionnel du cycle CRUD complet pour un client."""
    client_controller = ClientController()
    
    # 1. Création d'un client
    client_data = {
        "fullname": "New Client",
        "email": "new@client.com",
        "phone_number": 987654321,
        "enterprise": "New Enterprise"
    }
    
    client = client_controller.create(auth_token_commercial, db_session, client_data)
    
    # Vérifications de la création
    assert client is not None
    assert client.fullname == client_data["fullname"]
    assert client.email == client_data["email"]
    client_id = client.id
    
    # 2. Lecture du client
    retrieved_client = client_controller.get(auth_token_commercial, db_session, client_id)
    assert retrieved_client is not None
    assert retrieved_client.id == client_id
    assert retrieved_client.fullname == client_data["fullname"]
    
    # 3. Mise à jour du client
    update_data = {
        "fullname": "Updated Client",
        "email": "updated@client.com",
        "enterprise": "Updated Enterprise"
    }
    
    updated_client = client_controller.update_client(db_session, auth_token_commercial, client_id, update_data)
    assert updated_client is not None
    assert updated_client.fullname == update_data["fullname"]
    assert updated_client.email == update_data["email"]
    assert updated_client.enterprise == update_data["enterprise"]
    
    # 4. Suppression du client
    result = client_controller.delete_client(db_session, auth_token_commercial, client_id)
    assert result is True
    
    # Vérification que le client a bien été supprimé
    deleted_client = client_controller.get(auth_token_commercial, db_session, client_id)
    assert deleted_client is None

def test_permissions_commercial_vs_support(db_session, auth_token_commercial, auth_token_support, test_client):
    """Test fonctionnel des permissions entre commercial et support."""
    client_controller = ClientController()
    
    # 1. Le commercial peut créer un client
    client_data = {
        "fullname": "Permission Test Client",
        "email": "permission@test.com",
        "phone_number": 123456789,
        "enterprise": "Permission Test Enterprise"
    }
    
    client = client_controller.create(auth_token_commercial, db_session, client_data)
    assert client is not None
    
    # 2. Le support ne peut pas créer un client
    support_client = client_controller.create(auth_token_support, db_session, {
        "fullname": "Support Client",
        "email": "support@client.com",
        "phone_number": 987654321,
        "enterprise": "Support Enterprise"
    })
    assert support_client is None
    
    # 3. Le support peut lire un client
    read_client = client_controller.get(auth_token_support, db_session, test_client.id)
    assert read_client is not None
    assert read_client.id == test_client.id
    
    # 4. Le support ne peut pas modifier un client
    update_result = client_controller.update_client(db_session, auth_token_support, test_client.id, {
        "fullname": "Support Updated Client"
    })
    assert update_result is None
    
    # 5. Le support ne peut pas supprimer un client
    delete_result = client_controller.delete_client(db_session, auth_token_support, test_client.id)
    assert delete_result is False 