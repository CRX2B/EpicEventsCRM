from typing import Optional, Dict
from sqlalchemy.orm import Session
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.utils.auth import generate_token, verify_token
from epiceventsCRM.utils.permissions import Department, has_permission

class AuthController:
    """
    Contrôleur pour la gestion de l'authentification et des autorisations.
    """
    
    def __init__(self):
        self.user_dao = UserDAO()
    
    def login(self, db: Session, email: str, password: str) -> Optional[Dict]:
        """
        Authentifie un utilisateur et génère un token JWT.
        
        Args:
            db (Session): La session de base de données
            email (str): L'email de l'utilisateur
            password (str): Le mot de passe
            
        Returns:
            Optional[Dict]: Les informations de l'utilisateur et le token si authentifié, None sinon
        """
        user = self.user_dao.authenticate(db, email, password)
        if not user:
            return None
            
        # Récupération du nom du département
        department_name = user.department.departement_name if user.department else None
        if not department_name:
            return None
            
        # Génération du token
        token = generate_token(user.id, department_name)
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "fullname": user.fullname,
                "department": department_name
            },
            "token": token
        }
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Vérifie un token JWT.
        
        Args:
            token (str): Le token à vérifier
            
        Returns:
            Optional[Dict]: Les données du token si valide, None sinon
        """
        return verify_token(token)
    
    def check_permission(self, token: str, permission: str) -> bool:
        """
        Vérifie si l'utilisateur a une permission spécifique.
        
        Args:
            token (str): Le token JWT
            permission (str): La permission à vérifier
            
        Returns:
            bool: True si l'utilisateur a la permission, False sinon
        """
        payload = self.verify_token(token)
        if not payload:
            return False

        # Récupération du département depuis le token
        try:
            department = Department(payload["department"])
            return has_permission(department, permission)
        except ValueError:
            return False 