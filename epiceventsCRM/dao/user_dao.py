from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from epiceventsCRM.dao.base_dao import BaseDAO
from epiceventsCRM.models.models import User
from epiceventsCRM.utils.auth import hash_password, verify_password

class UserDAO(BaseDAO[User]):
    """
    DAO pour la gestion des utilisateurs.
    Hérite de BaseDAO et ajoute des méthodes spécifiques aux utilisateurs.
    """
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Récupère un utilisateur par son email.
        
        Args:
            db (Session): La session de base de données
            email (str): L'email de l'utilisateur
            
        Returns:
            Optional[User]: L'utilisateur si trouvé, None sinon
        """
        return db.scalar(select(User).where(User.email == email))
    
    def create(self, db: Session, obj_in: dict) -> User:
        """
        Crée un nouvel utilisateur.
        
        Args:
            db (Session): La session de base de données
            obj_in (dict): Les données de l'utilisateur
            
        Returns:
            User: L'utilisateur créé
        """
        # Hashage du mot de passe
        hashed_password = hash_password(obj_in["password"])
        
        # Création de l'utilisateur avec le mot de passe hashé
        user = User(
            fullname=obj_in["fullname"],
            email=obj_in["email"],
            password=hashed_password,
            departement_id=obj_in["departement_id"]
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def authenticate(self, db: Session, email: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur par son email et mot de passe.
        
        Args:
            db (Session): La session de base de données
            email (str): L'email de l'utilisateur
            password (str): Le mot de passe en clair
            
        Returns:
            Optional[User]: L'utilisateur si authentifié, None sinon
        """
        user = self.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    def update_password(self, db: Session, user_id: int, new_password: str) -> Optional[User]:
        """
        Met à jour le mot de passe d'un utilisateur.
        
        Args:
            db (Session): La session de base de données
            user_id (int): L'ID de l'utilisateur
            new_password (str): Le nouveau mot de passe en clair
            
        Returns:
            Optional[User]: L'utilisateur mis à jour si trouvé, None sinon
        """
        user = self.get(db, user_id)
        if not user:
            return None
        user.password = hash_password(new_password)
        db.commit()
        db.refresh(user)
        return user

    def verify_password(self, user: User, password: str) -> bool:
        """
        Vérifie le mot de passe d'un utilisateur.

        Args:
            user (User): L'utilisateur
            password (str): Le mot de passe à vérifier

        Returns:
            bool: True si le mot de passe correspond, False sinon
        """
        return verify_password(password, user.password) 