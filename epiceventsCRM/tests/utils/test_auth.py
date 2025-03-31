import pytest
from datetime import datetime, timedelta, timezone
import jwt
from epiceventsCRM.utils.auth import (
    hash_password,
    verify_password,
    generate_token,
    verify_token
)

def test_hash_password():
    """Test le hashage des mots de passe."""
    password = "test_password"
    hashed = hash_password(password)
    assert hashed != password
    assert isinstance(hashed, str)
    assert len(hashed) > 0

def test_verify_password():
    """Test la vérification des mots de passe."""
    password = "test_password"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_generate_and_verify_token():
    """Test la génération et la vérification des tokens JWT."""
    user_id = 1
    department = "commercial"
    
    # Génération du token
    token = generate_token(user_id, department)
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Vérification du token
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["department"] == department
    assert "exp" in payload

def test_verify_invalid_token():
    """Test la vérification d'un token invalide."""
    assert verify_token("invalid_token") is None

def test_verify_expired_token():
    """Test la vérification d'un token expiré."""
    # Création d'un token expiré
    payload = {
        "sub": 1,
        "department": "commercial",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    # Génération du token avec le payload expiré
    token = jwt.encode(payload, "test_secret", algorithm="HS256")
    assert verify_token(token) is None 