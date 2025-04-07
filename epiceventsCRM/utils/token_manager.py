import os
import json
import jwt
from typing import Optional, Dict, Any

# Chemin du fichier contenant le token JWT
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.token')

def save_token(token: str) -> None:
    """
    Sauvegarde le token JWT dans un fichier
    
    Args:
        token: Le token JWT à sauvegarder
    """
    with open(TOKEN_FILE, 'w') as file:
        json.dump({"token": token}, file)

def get_token() -> Optional[str]:
    """
    Récupère le token JWT depuis le fichier
    
    Returns:
        str ou None: Le token JWT s'il existe, None sinon
    """
    if not os.path.exists(TOKEN_FILE):
        return None
        
    try:
        with open(TOKEN_FILE, 'r') as file:
            data = json.load(file)
            return data.get("token")
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def clear_token() -> None:
    """
    Supprime le token JWT
    """
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        
def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Décode un token JWT sans vérifier la signature
    
    Args:
        token: Le token JWT à décoder
        
    Returns:
        Dict ou None: Le contenu du token s'il est valide, None sinon
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except (jwt.PyJWTError, AttributeError):
        return None
        
def generate_token(user_id: int, department: str) -> str:
    """
    Génère un token JWT pour les tests
    
    Args:
        user_id: ID de l'utilisateur
        department: Département de l'utilisateur
        
    Returns:
        str: Token JWT généré
    """
    payload = {
        "user_id": user_id,
        "department": department
    }
    return jwt.encode(payload, "secret_key_for_tests") 