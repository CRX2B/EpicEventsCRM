import pytest
from datetime import datetime
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.models.models import Client, User
from time import sleep

def test_create_client(db_session):
    """Test la création d'un client."""
    # Création d'un utilisateur commercial (pour le sales_contact)
    user = User(fullname="Test Commercial", email="test@example.com", password="password")
    db_session.add(user)
    db_session.commit()
    
    # Données du client
    client_data = {
        "fullname": "Test Client",
        "email": "client@example.com",
        "phone_number": 123456789,
        "enterprise": "Test Enterprise",
        "sales_contact_id": user.id
    }
    
    # Création du client
    client_dao = ClientDAO()
    client = client_dao.create(db_session, client_data)
    
    # Vérifications
    assert client.id is not None
    assert client.fullname == client_data["fullname"]
    assert client.email == client_data["email"]
    assert client.phone_number == client_data["phone_number"]
    assert client.enterprise == client_data["enterprise"]
    assert client.sales_contact_id == user.id
    assert client.create_date is not None
    assert client.update_date is not None

def test_get_client(db_session):
    """Test la récupération d'un client par son ID."""
    # Création d'un utilisateur commercial (pour le sales_contact)
    user = User(fullname="Test Commercial", email="test2@example.com", password="password")
    db_session.add(user)
    db_session.commit()
    
    # Création d'un client
    client = Client(
        fullname="Test Client",
        email="client2@example.com",
        phone_number=987654321,
        enterprise="Test Enterprise",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=user.id
    )
    db_session.add(client)
    db_session.commit()
    
    # Récupération du client
    client_dao = ClientDAO()
    retrieved_client = client_dao.get(db_session, client.id)
    
    # Vérifications
    assert retrieved_client is not None
    assert retrieved_client.id == client.id
    assert retrieved_client.fullname == client.fullname
    assert retrieved_client.email == client.email
    assert retrieved_client.phone_number == client.phone_number

def test_get_client_not_found(db_session):
    """Test la récupération d'un client qui n'existe pas."""
    client_dao = ClientDAO()
    client = client_dao.get(db_session, 999)
    assert client is None

def test_get_by_email(db_session):
    """Test la récupération d'un client par son email."""
    # Création d'un utilisateur commercial (pour le sales_contact)
    user = User(fullname="Test Commercial", email="test3@example.com", password="password")
    db_session.add(user)
    db_session.commit()
    
    # Création d'un client
    email = "client3@example.com"
    client = Client(
        fullname="Test Client",
        email=email,
        phone_number=987654321,
        enterprise="Test Enterprise",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=user.id
    )
    db_session.add(client)
    db_session.commit()
    
    # Récupération du client par email
    client_dao = ClientDAO()
    retrieved_client = client_dao.get_by_email(db_session, email)
    
    # Vérifications
    assert retrieved_client is not None
    assert retrieved_client.id == client.id
    assert retrieved_client.email == email

def test_get_all(db_session):
    """Test la récupération de tous les clients."""
    # Création d'un utilisateur commercial (pour le sales_contact)
    user = User(fullname="Test Commercial", email="test4@example.com", password="password")
    db_session.add(user)
    db_session.commit()
    
    # Création de plusieurs clients
    clients = []
    for i in range(5):
        client = Client(
            fullname=f"Test Client {i}",
            email=f"client{i}@example.com",
            phone_number=i,
            enterprise=f"Test Enterprise {i}",
            create_date=datetime.now(),
            update_date=datetime.now(),
            sales_contact_id=user.id
        )
        db_session.add(client)
        clients.append(client)
    db_session.commit()
    
    # Récupération de tous les clients
    client_dao = ClientDAO()
    all_clients = client_dao.get_all(db_session)
    
    # Vérifications
    assert len(all_clients) >= 5  # Il peut y avoir d'autres clients des tests précédents

def test_get_by_sales_contact(db_session):
    """Test la récupération des clients gérés par un commercial."""
    # Création de deux utilisateurs commerciaux
    user1 = User(fullname="Commercial 1", email="commercial1@example.com", password="password")
    user2 = User(fullname="Commercial 2", email="commercial2@example.com", password="password")
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    
    # Création de clients pour chaque commercial
    for i in range(3):
        client1 = Client(
            fullname=f"Client of Commercial 1 - {i}",
            email=f"client1_{i}@example.com",
            phone_number=i,
            enterprise=f"Enterprise {i}",
            create_date=datetime.now(),
            update_date=datetime.now(),
            sales_contact_id=user1.id
        )
        db_session.add(client1)
        
    for i in range(2):
        client2 = Client(
            fullname=f"Client of Commercial 2 - {i}",
            email=f"client2_{i}@example.com",
            phone_number=i + 100,
            enterprise=f"Enterprise {i + 100}",
            create_date=datetime.now(),
            update_date=datetime.now(),
            sales_contact_id=user2.id
        )
        db_session.add(client2)
    
    db_session.commit()
    
    # Récupération des clients par commercial
    client_dao = ClientDAO()
    clients_of_user1 = client_dao.get_by_sales_contact(db_session, user1.id)
    clients_of_user2 = client_dao.get_by_sales_contact(db_session, user2.id)
    
    # Vérifications
    assert len(clients_of_user1) == 3
    assert len(clients_of_user2) == 2
    
    for client in clients_of_user1:
        assert client.sales_contact_id == user1.id
        
    for client in clients_of_user2:
        assert client.sales_contact_id == user2.id

def test_update_client(db_session):
    """Test la mise à jour d'un client."""
    # Création d'un utilisateur commercial (pour le sales_contact)
    user = User(fullname="Test Commercial", email="test5@example.com", password="password")
    db_session.add(user)
    db_session.commit()
    
    # Création d'un client
    client = Client(
        fullname="Original Name",
        email="original@example.com",
        phone_number=123456789,
        enterprise="Original Enterprise",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=user.id
    )
    db_session.add(client)
    db_session.commit()
    
    # Stockage de la date initiale pour comparaison
    initial_update_date = client.update_date
    
    # Ajout d'un délai pour garantir que la date de mise à jour sera différente
    sleep(0.1)
    
    # Données de mise à jour
    update_data = {
        "fullname": "Updated Name",
        "email": "updated@example.com",
        "enterprise": "Updated Enterprise"
    }
    
    # Mise à jour du client
    client_dao = ClientDAO()
    updated_client = client_dao.update(db_session, client, update_data)
    
    # Vérifications
    assert updated_client.id == client.id
    assert updated_client.fullname == update_data["fullname"]
    assert updated_client.email == update_data["email"]
    assert updated_client.enterprise == update_data["enterprise"]
    assert updated_client.phone_number == client.phone_number  # Inchangé
    
    # Vérification que les dates sont différentes
    assert updated_client.update_date != initial_update_date

def test_delete_client(db_session):
    """Test la suppression d'un client."""
    # Création d'un utilisateur commercial (pour le sales_contact)
    user = User(fullname="Test Commercial", email="test6@example.com", password="password")
    db_session.add(user)
    db_session.commit()
    
    # Création d'un client
    client = Client(
        fullname="Client to Delete",
        email="delete@example.com",
        phone_number=123456789,
        enterprise="Delete Enterprise",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=user.id
    )
    db_session.add(client)
    db_session.commit()
    
    # Suppression du client
    client_dao = ClientDAO()
    result = client_dao.delete(db_session, client.id)
    
    # Vérifications
    assert result is True
    assert client_dao.get(db_session, client.id) is None

def test_delete_client_not_found(db_session):
    """Test la suppression d'un client qui n'existe pas."""
    client_dao = ClientDAO()
    result = client_dao.delete(db_session, 999)
    assert result is False 