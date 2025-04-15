import json
import os
import pytest
import jwt

from epiceventsCRM.utils.token_manager import (
    TOKEN_FILE,
    save_token,
    get_token,
    clear_token,
    decode_token,
    generate_token,
)


@pytest.fixture
def mock_token_file(monkeypatch, tmp_path):
    """Fixture qui redéfinit TOKEN_FILE vers un chemin temporaire."""
    token_file = tmp_path / ".token"
    monkeypatch.setattr("epiceventsCRM.utils.token_manager.TOKEN_FILE", str(token_file))
    return token_file


def test_save_token(mock_token_file):
    """Test de la sauvegarde du token."""
    test_token = "test.jwt.token"
    save_token(test_token)

    # Vérifier que le fichier existe et contient le bon token
    assert os.path.exists(mock_token_file)
    with open(mock_token_file, "r") as file:
        data = json.load(file)
        assert data.get("token") == test_token


def test_get_token(mock_token_file):
    """Test de la récupération du token."""
    # Cas où le fichier n'existe pas
    if os.path.exists(mock_token_file):
        os.remove(mock_token_file)
    assert get_token() is None

    # Cas où le fichier existe
    test_token = "valid.jwt.token"
    with open(mock_token_file, "w") as file:
        json.dump({"token": test_token}, file)

    assert get_token() == test_token


def test_get_token_invalid_json(mock_token_file):
    """Test de la récupération du token avec un JSON invalide."""
    with open(mock_token_file, "w") as file:
        file.write("Invalid JSON")

    assert get_token() is None


def test_clear_token(mock_token_file):
    """Test de la suppression du token."""
    # Créer un fichier de token
    with open(mock_token_file, "w") as file:
        json.dump({"token": "test.token"}, file)

    # Vérifier que le fichier existe
    assert os.path.exists(mock_token_file)

    # Supprimer le token
    clear_token()

    # Vérifier que le fichier n'existe plus
    assert not os.path.exists(mock_token_file)


def test_clear_token_no_file(mock_token_file):
    """Test de la suppression du token quand le fichier n'existe pas."""
    if os.path.exists(mock_token_file):
        os.remove(mock_token_file)

    # Vérifier que l'appel ne lève pas d'exception
    clear_token()
    assert not os.path.exists(mock_token_file)


def test_decode_token():
    """Test du décodage d'un token valide."""
    # Création d'un token valide
    payload = {"user_id": 42, "department": "commercial"}
    token = jwt.encode(payload, "secret", algorithm="HS256")

    # Décodage du token
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["user_id"] == 42
    assert decoded["department"] == "commercial"


def test_decode_token_invalid():
    """Test du décodage d'un token invalide."""
    assert decode_token("invalid.token") is None


def test_generate_token():
    """Test de la génération d'un token."""
    user_id = 123
    department = "support"

    token = generate_token(user_id, department)
    assert isinstance(token, str)

    # Décodage du token pour vérifier son contenu
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == user_id
    assert decoded["department"] == department
