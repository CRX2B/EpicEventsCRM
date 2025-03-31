from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import User
from epiceventsCRM.utils.permissions import Department
from epiceventsCRM.controllers.auth_controller import AuthController

class UserManagementController:
    """
    Contrôleur pour la gestion des utilisateurs.
    Accessible uniquement au département gestion.
    """
    
    def __init__(self):
        self.user_dao = UserDAO()
        self.auth_controller = AuthController()
    
    def check_permission(self, token: str) -> bool:
        """
        Vérifie si l'utilisateur a la permission de gérer les utilisateurs.
        
        Args:
            token (str): Le token JWT
            
        Returns:
            bool: True si l'utilisateur a la permission, False sinon
        """
        return self.auth_controller.check_permission(token, "create_user")
    
    def create_user(self, db: Session, token: str, user_data: Dict) -> Optional[User]:
        """
        Crée un nouvel utilisateur.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            user_data (Dict): Les données de l'utilisateur
            
        Returns:
            Optional[User]: L'utilisateur créé si la permission est accordée, None sinon
        """
        if not self.check_permission(token):
            return None
        return self.user_dao.create(db, user_data)
    
    def get_user(self, db: Session, token: str, user_id: int) -> Optional[User]:
        """
        Récupère un utilisateur par son ID.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            user_id (int): L'ID de l'utilisateur
            
        Returns:
            Optional[User]: L'utilisateur si trouvé et si la permission est accordée, None sinon
        """
        if not self.check_permission(token):
            return None
        return self.user_dao.get(db, user_id)
    
    def get_all_users(self, db: Session, token: str, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Récupère tous les utilisateurs.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            skip (int): Nombre d'utilisateurs à sauter
            limit (int): Nombre maximum d'utilisateurs à retourner
            
        Returns:
            List[User]: Liste des utilisateurs si la permission est accordée, liste vide sinon
        """
        if not self.check_permission(token):
            return []
        return self.user_dao.get_all(db, skip=skip, limit=limit)
    
    def update_user(self, db: Session, token: str, user_id: int, user_data: Dict) -> Optional[User]:
        """
        Met à jour un utilisateur.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            user_id (int): L'ID de l'utilisateur
            user_data (Dict): Les nouvelles données
            
        Returns:
            Optional[User]: L'utilisateur mis à jour si la permission est accordée, None sinon
        """
        if not self.check_permission(token):
            return None
        user = self.user_dao.get(db, user_id)
        if not user:
            return None
        return self.user_dao.update(db, user, user_data)
    
    def delete_user(self, db: Session, token: str, user_id: int) -> bool:
        """
        Supprime un utilisateur.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            user_id (int): L'ID de l'utilisateur
            
        Returns:
            bool: True si l'utilisateur a été supprimé et si la permission est accordée, False sinon
        """
        if not self.check_permission(token):
            return False
        return self.user_dao.delete(db, user_id) 