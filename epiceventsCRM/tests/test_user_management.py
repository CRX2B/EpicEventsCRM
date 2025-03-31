import pytest
from sqlalchemy.orm import Session
from epiceventsCRM.controllers.user_management_controller import UserManagementController
from epiceventsCRM.models.models import User, Department
from epiceventsCRM.utils.auth import generate_token

@pytest.fixture
def departments(db_session):
    """Crée les départements nécessaires pour les tests."""
    departments = [
        Department(departement_name="commercial"),
        Department(departement_name="support"),
        Department(departement_name="gestion")
    ]
    for dept in departments:
        db_session.add(dept)
    db_session.commit()
    return departments

@pytest.fixture
def user_management_controller():
    return UserManagementController()

@pytest.fixture
def gestion_token(departments):
    return generate_token(1, "gestion")

@pytest.fixture
def commercial_token(departments):
    return generate_token(2, "commercial")

@pytest.fixture
def support_token(departments):
    return generate_token(3, "support")

def test_create_user_with_gestion_permission(db_session, user_management_controller, gestion_token, departments):
    """Test la création d'un utilisateur avec les permissions de gestion."""
    user_data = {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "test_password",
        "departement_id": departments[2].id  # Utilisation de l'ID du département gestion
    }
    
    user = user_management_controller.create_user(db_session, gestion_token, user_data)
    assert user is not None
    assert user.fullname == "Test User"
    assert user.email == "test@example.com"
    assert user.departement_id == departments[2].id

def test_create_user_without_permission(db_session, user_management_controller, commercial_token, departments):
    """Test la création d'un utilisateur sans les permissions de gestion."""
    user_data = {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "test_password",
        "departement_id": departments[2].id  # Utilisation de l'ID du département gestion
    }
    
    user = user_management_controller.create_user(db_session, commercial_token, user_data)
    assert user is None

def test_get_user_with_gestion_permission(db_session, user_management_controller, gestion_token, departments):
    """Test la récupération d'un utilisateur avec les permissions de gestion."""
    # Création d'un utilisateur de test
    user_data = {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "test_password",
        "departement_id": departments[2].id  # Utilisation de l'ID du département gestion
    }
    test_user = user_management_controller.create_user(db_session, gestion_token, user_data)
    
    # Récupération de l'utilisateur
    user = user_management_controller.get_user(db_session, gestion_token, test_user.id)
    assert user is not None
    assert user.id == test_user.id

def test_get_user_without_permission(db_session, user_management_controller, commercial_token):
    """Test la récupération d'un utilisateur sans les permissions de gestion."""
    user = user_management_controller.get_user(db_session, commercial_token, 1)
    assert user is None

def test_get_all_users_with_gestion_permission(db_session, user_management_controller, gestion_token, departments):
    """Test la récupération de tous les utilisateurs avec les permissions de gestion."""
    # Création de plusieurs utilisateurs
    for i in range(3):
        user_data = {
            "fullname": f"Test User {i}",
            "email": f"test{i}@example.com",
            "password": "test_password",
            "departement_id": departments[2].id  # Utilisation de l'ID du département gestion
        }
        user_management_controller.create_user(db_session, gestion_token, user_data)
    
    users = user_management_controller.get_all_users(db_session, gestion_token)
    assert len(users) >= 3

def test_get_all_users_without_permission(db_session, user_management_controller, commercial_token):
    """Test la récupération de tous les utilisateurs sans les permissions de gestion."""
    users = user_management_controller.get_all_users(db_session, commercial_token)
    assert len(users) == 0

def test_update_user_with_gestion_permission(db_session, user_management_controller, gestion_token, departments):
    """Test la mise à jour d'un utilisateur avec les permissions de gestion."""
    # Création d'un utilisateur de test
    user_data = {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "test_password",
        "departement_id": departments[2].id  # Utilisation de l'ID du département gestion
    }
    test_user = user_management_controller.create_user(db_session, gestion_token, user_data)
    
    # Mise à jour de l'utilisateur
    update_data = {
        "fullname": "Updated User",
        "email": "updated@example.com"
    }
    updated_user = user_management_controller.update_user(db_session, gestion_token, test_user.id, update_data)
    
    assert updated_user is not None
    assert updated_user.fullname == "Updated User"
    assert updated_user.email == "updated@example.com"

def test_update_user_without_permission(db_session, user_management_controller, commercial_token):
    """Test la mise à jour d'un utilisateur sans les permissions de gestion."""
    update_data = {
        "fullname": "Updated User",
        "email": "updated@example.com"
    }
    updated_user = user_management_controller.update_user(db_session, commercial_token, 1, update_data)
    assert updated_user is None

def test_delete_user_with_gestion_permission(db_session, user_management_controller, gestion_token, departments):
    """Test la suppression d'un utilisateur avec les permissions de gestion."""
    # Création d'un utilisateur de test
    user_data = {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "test_password",
        "departement_id": departments[2].id  # Utilisation de l'ID du département gestion
    }
    test_user = user_management_controller.create_user(db_session, gestion_token, user_data)
    
    # Suppression de l'utilisateur
    result = user_management_controller.delete_user(db_session, gestion_token, test_user.id)
    assert result is True
    
    # Vérification que l'utilisateur a été supprimé
    deleted_user = user_management_controller.get_user(db_session, gestion_token, test_user.id)
    assert deleted_user is None

def test_delete_user_without_permission(db_session, user_management_controller, commercial_token):
    """Test la suppression d'un utilisateur sans les permissions de gestion."""
    result = user_management_controller.delete_user(db_session, commercial_token, 1)
    assert result is False 