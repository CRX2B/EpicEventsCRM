import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import bcrypt
import jwt
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration JWT
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("La variable d'environnement JWT_SECRET n'est pas définie")

# Liste des algorithmes JWT sécurisés
SECURE_ALGORITHMS = ["HS256", "HS384", "HS512", "RS256", "ES256"]

# Récupération de l'algorithme depuis les variables d'environnement
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
if JWT_ALGORITHM not in SECURE_ALGORITHMS:
    raise ValueError(f"Algorithme JWT non sécurisé: {JWT_ALGORITHM}")

JWT_EXPIRATION_DELTA = timedelta(hours=24)


def hash_password(password: str) -> str:
    """
    Hash un mot de passe avec bcrypt.

    Args:
        password (str): Le mot de passe à hasher

    Returns:
        str: Le mot de passe hashé

    Raises:
        ValueError: Si le mot de passe est vide
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """
    Vérifie si un mot de passe correspond à son hash.

    Args:
        password (str): Le mot de passe à vérifier
        hashed (str): Le hash stocké

    Returns:
        bool: True si le mot de passe correspond, False sinon

    Raises:
        ValueError: Si le mot de passe ou le hash est vide
    """
    return bcrypt.checkpw(password.encode(), hashed.encode())


def generate_token(user_id: int, department: str) -> str:
    """
    Génère un token JWT.

    Args:
        user_id (int): L'ID de l'utilisateur
        department (str): Le département de l'utilisateur

    Returns:
        str: Le token JWT

    Raises:
        jwt.PyJWTError: Si la génération du token échoue
    """
    payload = {
        "sub": user_id,
        "department": department,
        "exp": datetime.now(timezone.utc) + JWT_EXPIRATION_DELTA,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[Dict]:
    """
    Vérifie un token JWT.

    Args:
        token (str): Le token à vérifier

    Returns:
        Optional[Dict]: Les données du token si valide, None sinon

    Raises:
        jwt.ExpiredSignatureError: Si le token est expiré
        jwt.PyJWTError: Si le token est invalide
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None
