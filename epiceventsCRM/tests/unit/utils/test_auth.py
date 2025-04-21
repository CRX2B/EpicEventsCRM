import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
import bcrypt
import jwt
from dotenv import load_dotenv

from epiceventsCRM.utils.auth import (
    hash_password,
    verify_password,
    generate_token,
    verify_token,
    JWT_SECRET,
    JWT_ALGORITHM,
)


load_dotenv()


class TestAuthUtils:
    """Tests unitaires pour les utilitaires d'authentification."""

    def test_hash_password(self):
        """Teste le hachage d'un mot de passe."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert bcrypt.checkpw(password.encode(), hashed.encode())

    def test_verify_password_correct(self):
        """Teste la vérification d'un mot de passe correct."""
        password = "mysecretpassword"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Teste la vérification d'un mot de passe incorrect."""
        password = "mysecretpassword"
        wrong_password = "wrongpassword"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        assert verify_password(wrong_password, hashed) is False

    def test_generate_token(self):
        """Teste la génération d'un token JWT."""
        user_id = 123
        department = "gestion"
        token = generate_token(user_id, department)
        assert isinstance(token, str)

        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == user_id
        assert payload["department"] == department
        assert "exp" in payload

    def test_verify_token_valid(self):
        """Teste la vérification d'un token JWT valide."""
        user_id = 123
        department = "commercial"
        token = generate_token(user_id, department)
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["department"] == department

    def test_verify_token_expired(self):
        """Teste la vérification d'un token JWT expiré."""
        user_id = 123
        department = "support"

        past_exp = datetime.now(timezone.utc) - timedelta(hours=1)
        payload_data = {"sub": user_id, "department": department, "exp": past_exp}
        expired_token = jwt.encode(payload_data, JWT_SECRET, algorithm=JWT_ALGORITHM)

        payload = verify_token(expired_token)
        assert payload is None

    def test_verify_token_invalid_signature(self):
        """Teste la vérification d'un token JWT avec une signature invalide."""
        user_id = 123
        department = "gestion"
        payload_data = {
            "sub": user_id,
            "department": department,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        invalid_token = jwt.encode(payload_data, "wrong_secret", algorithm=JWT_ALGORITHM)

        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_token_invalid_format(self):
        """Teste la vérification d'un token mal formaté."""
        invalid_token = "this.is.not.a.valid.token"
        payload = verify_token(invalid_token)
        assert payload is None
