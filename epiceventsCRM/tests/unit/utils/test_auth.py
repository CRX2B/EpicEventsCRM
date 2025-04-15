import pytest
import jwt
from datetime import datetime, timedelta, timezone

from epiceventsCRM.utils.auth import hash_password, verify_password, generate_token, verify_token


class TestAuth:
    def test_hash_password(self):
        """Vérifie que le hash d'un mot de passe génère un résultat différent du mot de passe original."""
        password = "secure_password123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # Le préfixe bcrypt

    def test_verify_password(self):
        """Vérifie que la validation du mot de passe fonctionne correctement."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        # Test du bon mot de passe
        assert verify_password(password, hashed) is True

        # Test d'un mauvais mot de passe
        assert verify_password(wrong_password, hashed) is False

    def test_token_lifecycle(self, monkeypatch):
        """Test le cycle de vie complet d'un token: génération et vérification."""
        # Configuration d'un secret de test
        test_secret = "test_secret"
        monkeypatch.setattr("epiceventsCRM.utils.auth.JWT_SECRET", test_secret)
        monkeypatch.setattr("epiceventsCRM.utils.auth.JWT_ALGORITHM", "HS256")

        # Données de test
        user_id = 42
        department = "commercial"

        # Génération du token
        token = generate_token(user_id, department)
        assert isinstance(token, str)

        # Vérification du token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["department"] == department
        assert "exp" in payload

    def test_verify_invalid_token(self):
        """Vérifie que la validation d'un token invalide échoue."""
        assert verify_token("invalid.token.string") is None

    def test_verify_expired_token(self, monkeypatch):
        """Vérifie que la validation d'un token expiré échoue."""
        # Configuration d'un secret de test
        test_secret = "test_secret"
        monkeypatch.setattr("epiceventsCRM.utils.auth.JWT_SECRET", test_secret)

        # Création d'un token expiré
        payload = {
            "sub": 1,
            "department": "commercial",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }

        expired_token = jwt.encode(payload, test_secret, algorithm="HS256")

        # Vérification du token expiré
        assert verify_token(expired_token) is None
