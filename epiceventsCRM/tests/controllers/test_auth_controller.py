import pytest
from datetime import datetime, timedelta
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.models.models import User, Department
from epiceventsCRM.utils.auth import generate_token, verify_token

def test_user_creation_and_authentication(db_session, test_department):
    """Test la création d'un utilisateur et son authentification."""
    # Création d'un utilisateur
    user_dao = UserDAO()
    user_data = {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "test_password",
        "departement_id": test_department.id
    }
    user = user_dao.create(db_session, user_data)
    
    # Vérification que le mot de passe est hashé
    assert user.password != "test_password"
    
    # Test de l'authentification
    authenticated_user = user_dao.authenticate(db_session, "test@example.com", "test_password")
    assert authenticated_user is not None
    assert authenticated_user.email == "test@example.com"

def test_auth_controller_login(db_session, test_department):
    """Test le processus de login via le contrôleur."""
    auth_controller = AuthController()
    
    # Création d'un utilisateur
    user_dao = UserDAO()
    user_data = {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "test_password",
        "departement_id": test_department.id
    }
    user_dao.create(db_session, user_data)
    
    # Test du login
    result = auth_controller.login(db_session, "test@example.com", "test_password")
    assert result is not None
    assert "token" in result
    assert "user" in result
    assert result["user"]["email"] == "test@example.com"
    assert result["user"]["fullname"] == "Test User"
    assert result["user"]["department"] == test_department.departement_name

def test_auth_controller_permissions(db_session, test_department):
    """Test la vérification des permissions via le contrôleur."""
    auth_controller = AuthController()

    # Création d'un utilisateur commercial
    user_dao = UserDAO()
    commercial_data = {
        "fullname": "Commercial User",
        "email": "commercial@example.com",
        "password": "test_password",
        "departement_id": test_department.id
    }
    user_dao.create(db_session, commercial_data)

    # Login et récupération du token
    result = auth_controller.login(db_session, commercial_data["email"], commercial_data["password"])
    token = result["token"]

    # Test des permissions
    assert auth_controller.check_permission(token, "create_client") is True
    assert auth_controller.check_permission(token, "read_client") is True
    assert auth_controller.check_permission(token, "update_client") is True
    assert auth_controller.check_permission(token, "delete_client") is True
    assert auth_controller.check_permission(token, "create_contract") is True
    assert auth_controller.check_permission(token, "read_contract") is True
    assert auth_controller.check_permission(token, "update_contract") is True
    assert auth_controller.check_permission(token, "delete_contract") is False
    assert auth_controller.check_permission(token, "create_event") is False
    assert auth_controller.check_permission(token, "read_event") is True
    assert auth_controller.check_permission(token, "update_event") is False
    assert auth_controller.check_permission(token, "delete_event") is False

def test_invalid_login(db_session, test_department):
    """Test la tentative de login avec des identifiants invalides."""
    auth_controller = AuthController()
    
    # Création d'un utilisateur
    user_dao = UserDAO()
    user_data = {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "test_password",
        "departement_id": test_department.id
    }
    user_dao.create(db_session, user_data)
    
    # Test avec un mauvais mot de passe
    result = auth_controller.login(db_session, "test@example.com", "wrong_password")
    assert result is None
    
    # Test avec un email inexistant
    result = auth_controller.login(db_session, "nonexistent@example.com", "test_password")
    assert result is None 