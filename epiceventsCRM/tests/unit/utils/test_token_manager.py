import json
import os
from unittest.mock import patch, mock_open, call

import pytest
import jwt

from epiceventsCRM.utils.token_manager import (
    save_token,
    get_token,
    clear_token,
    TOKEN_FILE,
)


@pytest.fixture
def mock_token_file(monkeypatch):
    # Ce fixture n'est plus nécessaire
    pass


# Tests pour save_token
def test_save_token(mocker):
    """Vérifie que save_token appelle open et json.dump correctement."""
    mock_file_handle = mock_open().return_value  # Obtenir le handle mocké
    mock_open_func = mocker.patch("builtins.open", return_value=mock_file_handle)
    mock_json_dump = mocker.patch("json.dump")
    test_token = "mon_token_test"
    expected_data = {"token": test_token}

    save_token(test_token)

    # Vérifier que open a été appelé pour écrire dans le bon fichier
    mock_open_func.assert_called_once_with(TOKEN_FILE, "w")
    # Vérifier que json.dump a été appelé avec les bonnes données et le handle
    mock_json_dump.assert_called_once_with(expected_data, mock_file_handle)


# Tests pour get_token
def test_get_token_exists(mocker):
    """Vérifie que get_token lit et retourne le token si le fichier existe."""
    test_token = "mon_token_test"
    file_content = json.dumps({"token": test_token})
    mock_file = mock_open(read_data=file_content)
    mocker.patch("builtins.open", mock_file)
    mocker.patch("os.path.exists", return_value=True)

    token = get_token()

    os.path.exists.assert_called_once_with(TOKEN_FILE)
    mock_file.assert_called_once_with(TOKEN_FILE, "r")
    assert token == test_token


def test_get_token_not_exists(mocker):
    """Vérifie que get_token retourne None si le fichier n'existe pas."""
    mocker.patch("os.path.exists", return_value=False)
    mock_file = mocker.patch("builtins.open")  # Pour s'assurer qu'il n'est pas appelé

    token = get_token()

    os.path.exists.assert_called_once_with(TOKEN_FILE)
    mock_file.assert_not_called()
    assert token is None


def test_get_token_invalid_json(mocker):
    """Vérifie que get_token retourne None si le fichier contient du JSON invalide."""
    mock_file = mock_open(read_data="pas du json")
    mocker.patch("builtins.open", mock_file)
    mocker.patch("os.path.exists", return_value=True)

    token = get_token()

    os.path.exists.assert_called_once_with(TOKEN_FILE)
    mock_file.assert_called_once_with(TOKEN_FILE, "r")
    assert token is None


def test_get_token_file_not_found_on_read(mocker):
    """Vérifie la gestion de FileNotFoundError lors de la lecture."""
    # Simule que le fichier existe au début mais disparaît avant lecture
    mocker.patch("os.path.exists", return_value=True)
    mock_open_func = mocker.patch("builtins.open", side_effect=FileNotFoundError)

    token = get_token()

    os.path.exists.assert_called_once_with(TOKEN_FILE)
    mock_open_func.assert_called_once_with(TOKEN_FILE, "r")
    assert token is None


# Tests pour clear_token
def test_clear_token_exists(mocker):
    """Vérifie que clear_token supprime le fichier s'il existe."""
    mocker.patch("os.path.exists", return_value=True)
    mock_remove = mocker.patch("os.remove")

    clear_token()

    os.path.exists.assert_called_once_with(TOKEN_FILE)
    mock_remove.assert_called_once_with(TOKEN_FILE)


def test_clear_token_not_exists(mocker):
    """Vérifie que clear_token ne fait rien si le fichier n'existe pas."""
    mocker.patch("os.path.exists", return_value=False)
    mock_remove = mocker.patch("os.remove")

    clear_token()

    os.path.exists.assert_called_once_with(TOKEN_FILE)
    mock_remove.assert_not_called()
