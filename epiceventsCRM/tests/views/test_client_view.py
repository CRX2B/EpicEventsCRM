import pytest
from epiceventsCRM.views.client_view import ClientView
from epiceventsCRM.models.models import User, Department, Client
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.utils.auth import hash_password
from datetime import datetime

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
        "email": "commercial_view@test.com",
        "password": hash_password("password123"),
        "departement_id": commercial_dept.id
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    
    return user

@pytest.fixture
def test_client(db_session, user_commercial):
    """Fixture pour créer un client de test."""
    client = Client(
        fullname="Test Client View",
        email="client_view@test.com",
        phone_number=555666777,
        enterprise="Test Enterprise View",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=user_commercial.id
    )
    db_session.add(client)
    db_session.commit()
    
    return client

@pytest.fixture
def auth_token(db_session, user_commercial):
    """Fixture pour générer un token JWT."""
    from epiceventsCRM.controllers.auth_controller import AuthController
    auth_controller = AuthController()
    token = auth_controller.login(db_session, user_commercial.email, "password123")
    return token["token"]

def test_display_client(test_client):
    """Test l'affichage d'un client."""
    client_view = ClientView()
    
    result = client_view.display_client(test_client)
    
    # Vérifications
    assert result["id"] == test_client.id
    assert result["fullname"] == test_client.fullname
    assert result["email"] == test_client.email
    assert result["phone_number"] == test_client.phone_number
    assert result["enterprise"] == test_client.enterprise
    assert "create_date" in result
    assert "update_date" in result
    assert result["sales_contact_id"] == test_client.sales_contact_id

def test_display_clients(db_session, user_commercial):
    """Test l'affichage de plusieurs clients."""
    client_view = ClientView()
    
    # Création de plusieurs clients
    clients = []
    for i in range(3):
        client = Client(
            fullname=f"Multiple Client {i}",
            email=f"multiple{i}@test.com",
            phone_number=i + 100000,
            enterprise=f"Multiple Enterprise {i}",
            create_date=datetime.now(),
            update_date=datetime.now(),
            sales_contact_id=user_commercial.id
        )
        db_session.add(client)
        clients.append(client)
    db_session.commit()
    
    result = client_view.display_clients(clients)
    
    # Vérifications
    assert len(result) == 3
    for i, client_dict in enumerate(result):
        assert client_dict["id"] == clients[i].id
        assert client_dict["fullname"] == clients[i].fullname
        assert client_dict["email"] == clients[i].email

def test_create_client(db_session, auth_token):
    """Test la création d'un client via la vue."""
    client_view = ClientView()
    
    client_data = {
        "fullname": "New View Client",
        "email": "new_view@client.com",
        "phone_number": 123123123,
        "enterprise": "New View Enterprise"
    }
    
    result = client_view.create_client(db_session, auth_token, client_data)
    
    # Vérifications
    assert "message" in result
    assert "Client créé avec succès" in result["message"]
    assert "client" in result
    assert result["client"]["fullname"] == client_data["fullname"]
    assert result["client"]["email"] == client_data["email"]
    assert result["client"]["phone_number"] == client_data["phone_number"]
    assert result["client"]["enterprise"] == client_data["enterprise"]

def test_create_client_missing_fields(db_session, auth_token):
    """Test la création d'un client avec des champs manquants."""
    client_view = ClientView()
    
    # Données incomplètes (manque phone_number)
    client_data = {
        "fullname": "Incomplete Client",
        "email": "incomplete@client.com",
        "enterprise": "Incomplete Enterprise"
    }
    
    result = client_view.create_client(db_session, auth_token, client_data)
    
    # Vérifications
    assert "error" in result
    assert "Le champ 'phone_number' est obligatoire" in result["error"]

def test_get_client(db_session, auth_token, test_client):
    """Test la récupération d'un client via la vue."""
    client_view = ClientView()
    
    result = client_view.get_client(db_session, auth_token, test_client.id)
    
    # Vérifications
    assert "client" in result
    assert result["client"]["id"] == test_client.id
    assert result["client"]["fullname"] == test_client.fullname
    assert result["client"]["email"] == test_client.email

def test_get_client_not_found(db_session, auth_token):
    """Test la récupération d'un client inexistant."""
    client_view = ClientView()
    
    result = client_view.get_client(db_session, auth_token, 9999)
    
    # Vérifications
    assert "error" in result
    assert "Client non trouvé" in result["error"]

def test_get_all_clients(db_session, auth_token, test_client):
    """Test la récupération de tous les clients via la vue."""
    client_view = ClientView()
    
    result = client_view.get_all_clients(db_session, auth_token)
    
    # Vérifications
    assert "clients" in result
    assert "count" in result
    assert result["count"] >= 1
    
    # Vérification que le client de test est bien présent
    client_ids = [c["id"] for c in result["clients"]]
    assert test_client.id in client_ids

def test_update_client(db_session, auth_token, test_client):
    """Test la mise à jour d'un client via la vue."""
    client_view = ClientView()
    
    update_data = {
        "fullname": "Updated View Client",
        "email": "updated_view@client.com",
        "enterprise": "Updated View Enterprise"
    }
    
    result = client_view.update_client(db_session, auth_token, test_client.id, update_data)
    
    # Vérifications
    assert "message" in result
    assert "Client mis à jour avec succès" in result["message"]
    assert "client" in result
    assert result["client"]["fullname"] == update_data["fullname"]
    assert result["client"]["email"] == update_data["email"]
    assert result["client"]["enterprise"] == update_data["enterprise"]

def test_delete_client(db_session, auth_token, user_commercial):
    """Test la suppression d'un client via la vue."""
    client_view = ClientView()
    
    # Création d'un client à supprimer
    client = Client(
        fullname="View Client to Delete",
        email="view_delete@client.com",
        phone_number=999999999,
        enterprise="View Delete Enterprise",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=user_commercial.id
    )
    db_session.add(client)
    db_session.commit()
    
    result = client_view.delete_client(db_session, auth_token, client.id)
    
    # Vérifications
    assert "message" in result
    assert "Client supprimé avec succès" in result["message"] 