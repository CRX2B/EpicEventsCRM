from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import User
from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.utils.permissions import require_permission

class UserController(BaseController[User]):
    """
    Contrôleur unifié pour la gestion des utilisateurs.
    Accessible principalement au département gestion, avec certaines fonctionnalités
    accessibles à d'autres départements selon les permissions.
    """
    
    def __init__(self):
        """
        Initialise le contrôleur des utilisateurs avec le DAO approprié.
        """
        super().__init__(UserDAO(), "user")
    
    @require_permission("read_user")
    def get_by_email(self, token: str, db: Session, email: str) -> Optional[User]:
        """
        Récupère un utilisateur par son email.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            email (str): L'email de l'utilisateur
            
        Returns:
            Optional[User]: L'utilisateur si trouvé, None sinon
        """
        return self.dao.get_by_email(db, email)
    
    @require_permission("create_user")
    def create_with_department(self, token: str, db: Session, user_data: Dict, department_id: int) -> Optional[User]:
        """
        Crée un utilisateur avec un département spécifique.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            user_data (Dict): Les données de l'utilisateur
            department_id (int): L'ID du département
            
        Returns:
            Optional[User]: L'utilisateur créé
        """
        user_data["departement_id"] = department_id
        return self.dao.create(db, user_data)
    
    @require_permission("update_user")
    def update_password(self, token: str, db: Session, user_id: int, new_password: str) -> Optional[User]:
        """
        Met à jour le mot de passe d'un utilisateur.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            user_id (int): L'ID de l'utilisateur
            new_password (str): Le nouveau mot de passe
            
        Returns:
            Optional[User]: L'utilisateur mis à jour si autorisé, None sinon
        """
        return self.dao.update_password(db, user_id, new_password)
    
    @require_permission("read_user")
    def get_users_by_department(self, token: str, db: Session, department_id: int) -> List[User]:
        """
        Récupère les utilisateurs d'un département spécifique.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            department_id (int): L'ID du département
            
        Returns:
            List[User]: Liste des utilisateurs du département
        """
        users = self.get_all(token, db)
        return [user for user in users if user.departement_id == department_id]
    
    def authenticate(self, db: Session, email: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur par son email et mot de passe.
        Ne nécessite pas de token car utilisé pour la connexion.
        
        Args:
            db (Session): La session de base de données
            email (str): L'email de l'utilisateur
            password (str): Le mot de passe
            
        Returns:
            Optional[User]: L'utilisateur si authentifié, None sinon
        """
        return self.dao.authenticate(db, email, password) 