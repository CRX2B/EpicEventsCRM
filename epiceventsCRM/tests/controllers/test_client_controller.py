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

def test_create_client_as_commercial(db_session, auth_token_commercial):
    """Test la création d'un client par un commercial."""
    client_controller = ClientController()
    
    client_data = {
        "fullname": "New Client",
        "email": "new@client.com",
        "phone_number": 987654321,
        "enterprise": "New Enterprise"
    }
    
    client = client_controller.create_client(db_session, auth_token_commercial, client_data)
    
    # Vérifications
    assert client is not None
    assert client.fullname == client_data["fullname"]
    assert client.email == client_data["email"]
    assert client.phone_number == client_data["phone_number"]
    assert client.enterprise == client_data["enterprise"]
    assert client.create_date is not None
    assert client.update_date is not None

def test_create_client_as_support(db_session, auth_token_support):
    """Test la création d'un client par un support (non autorisé)."""
    client_controller = ClientController()
    
    client_data = {
        "fullname": "New Client",
        "email": "support@client.com",
        "phone_number": 987654321,
        "enterprise": "New Enterprise"
    }
    
    client = client_controller.create_client(db_session, auth_token_support, client_data)
    
    # Le support ne devrait pas pouvoir créer de client
    assert client is None

def test_get_client(db_session, auth_token_commercial, test_client):
    """Test la récupération d'un client."""
    client_controller = ClientController()
    
    client = client_controller.get_client(db_session, auth_token_commercial, test_client.id)
    
    # Vérifications
    assert client is not None
    assert client.id == test_client.id
    assert client.fullname == test_client.fullname
    assert client.email == test_client.email
    assert client.phone_number == test_client.phone_number
    assert client.enterprise == test_client.enterprise

def test_get_client_as_support(db_session, auth_token_support, test_client):
    """Test la récupération d'un client par un support (autorisé en lecture)."""
    client_controller = ClientController()
    
    client = client_controller.get_client(db_session, auth_token_support, test_client.id)
    
    # Le support devrait pouvoir lire les clients
    assert client is not None
    assert client.id == test_client.id

def test_get_all_clients(db_session, auth_token_commercial, test_client):
    """Test la récupération de tous les clients."""
    client_controller = ClientController()
    
    clients = client_controller.get_all_clients(db_session, auth_token_commercial)
    
    # Vérifications
    assert clients is not None
    assert len(clients) >= 1  # Au moins le client de test
    assert any(c.id == test_client.id for c in clients)

def test_get_my_clients(db_session, auth_token_commercial, user_commercial, test_client):
    """Test la récupération des clients d'un commercial."""
    client_controller = ClientController()
    
    # Création d'un autre client avec un autre commercial
    other_user = User(fullname="Other Commercial", email="other@test.com", password="password")
    db_session.add(other_user)
    db_session.commit()
    
    other_client = Client(
        fullname="Other Client",
        email="other@client.com",
        phone_number=111222333,
        enterprise="Other Enterprise",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=other_user.id
    )
    db_session.add(other_client)
    db_session.commit()
    
    # Récupération des clients du commercial
    clients = client_controller.get_my_clients(db_session, auth_token_commercial)
    
    # Vérifications
    assert clients is not None
    assert len(clients) >= 1  # Au moins le client de test
    assert any(c.id == test_client.id for c in clients)
    assert not any(c.id == other_client.id for c in clients)

def test_update_client(db_session, auth_token_commercial, test_client):
    """Test la mise à jour d'un client."""
    client_controller = ClientController()
    
    # Stockage de la date initiale pour comparaison
    initial_update_date = test_client.update_date
    
    # Ajout d'un délai pour garantir que la date de mise à jour sera différente
    sleep(0.1)
    
    update_data = {
        "fullname": "Updated Client",
        "email": "updated@client.com",
        "enterprise": "Updated Enterprise"
    }
    
    updated_client = client_controller.update_client(db_session, auth_token_commercial, test_client.id, update_data)
    
    # Vérifications
    assert updated_client is not None
    assert updated_client.id == test_client.id
    assert updated_client.fullname == update_data["fullname"]
    assert updated_client.email == update_data["email"]
    assert updated_client.enterprise == update_data["enterprise"]
    
    # Vérification que les dates sont différentes
    assert updated_client.update_date != initial_update_date

def test_update_client_as_support(db_session, auth_token_support, test_client):
    """Test la mise à jour d'un client par un support (non autorisé)."""
    client_controller = ClientController()
    
    update_data = {
        "fullname": "Support Updated",
        "email": "support_updated@client.com"
    }
    
    updated_client = client_controller.update_client(db_session, auth_token_support, test_client.id, update_data)
    
    # Le support ne devrait pas pouvoir mettre à jour un client
    assert updated_client is None

def test_delete_client(db_session, auth_token_commercial, user_commercial):
    """Test la suppression d'un client."""
    client_controller = ClientController()
    
    # Création d'un client à supprimer
    client = Client(
        fullname="Client to Delete",
        email="delete@client.com",
        phone_number=999888777,
        enterprise="Delete Enterprise",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=user_commercial.id
    )
    db_session.add(client)
    db_session.commit()
    
    # Suppression du client
    result = client_controller.delete_client(db_session, auth_token_commercial, client.id)
    
    # Vérifications
    assert result is True
    
    # Vérification que le client a bien été supprimé
    client_dao = ClientDAO()
    deleted_client = client_dao.get(db_session, client.id)
    assert deleted_client is None

def test_delete_client_as_support(db_session, auth_token_support, test_client):
    """Test la suppression d'un client par un support (non autorisé)."""
    client_controller = ClientController()
    
    result = client_controller.delete_client(db_session, auth_token_support, test_client.id)
    
    # Le support ne devrait pas pouvoir supprimer un client
    assert result is False
    
    # Vérification que le client n'a pas été supprimé
    client_dao = ClientDAO()
    client = client_dao.get(db_session, test_client.id)
    assert client is not None 