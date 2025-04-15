import json
import os
from typing import Any, Dict, Optional

import jwt

# Chemin du fichier contenant le token JWT
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".token")


def save_token(token: str) -> None:
    """
    Sauvegarde le token JWT dans un fichier.

    Args:
        token (str): Le token JWT à sauvegarder

    Raises:
        IOError: Si l'écriture du fichier échoue
    """
    with open(TOKEN_FILE, "w") as file:
        json.dump({"token": token}, file)


def get_token() -> Optional[str]:
    """
    Récupère le token JWT depuis le fichier.

    Returns:
        Optional[str]: Le token JWT s'il existe, None sinon

    Raises:
        json.JSONDecodeError: Si le fichier n'est pas un JSON valide
        FileNotFoundError: Si le fichier n'existe pas
    """
    if not os.path.exists(TOKEN_FILE):
        return None

    try:
        with open(TOKEN_FILE, "r") as file:
            data = json.load(file)
            return data.get("token")
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def clear_token() -> None:
    """
    Supprime le token JWT.

    Raises:
        OSError: Si la suppression du fichier échoue
    """
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Décode un token JWT sans vérifier la signature.

    Args:
        token (str): Le token JWT à décoder

    Returns:
        Optional[Dict[str, Any]]: Le contenu du token s'il est valide, None sinon

    Raises:
        jwt.PyJWTError: Si le token est invalide
        AttributeError: Si le token est mal formaté
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except (jwt.PyJWTError, AttributeError):
        return None


def generate_token(sub: int, department: str) -> str:
    """
    Génère un token JWT pour un utilisateur.

    Args:
        sub (int): ID de l'utilisateur
        department (str): Département de l'utilisateur

    Returns:
        str: Le token JWT généré

    Raises:
        jwt.PyJWTError: Si la génération du token échoue
    """
    payload = {"sub": sub, "department": department}
    return jwt.encode(payload, "secret_key_for_tests")
