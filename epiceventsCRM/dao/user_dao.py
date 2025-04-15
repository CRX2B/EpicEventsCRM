from typing import Optional, Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from epiceventsCRM.dao.base_dao import BaseDAO
from epiceventsCRM.models.models import User
from epiceventsCRM.utils.auth import hash_password, verify_password


class UserDAO(BaseDAO[User]):
    """
    DAO pour la gestion des utilisateurs.
    Hérite de BaseDAO et ajoute des méthodes spécifiques aux utilisateurs.
    """

    def __init__(self):
        """
        Initialise le DAO
        """
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

    def get(self, db: Session, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        return db.query(User).filter(User.id == user_id).first()

    def create(self, db: Session, user_data: Dict) -> User:
        """Crée un nouvel utilisateur"""
        # Hashage du mot de passe avant stockage
        hashed_password = hash_password(user_data["password"])
        user = User(
            fullname=user_data["fullname"],
            email=user_data["email"],
            password=hashed_password,
            departement_id=user_data["departement_id"],
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

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """
        Récupère un utilisateur par son ID en utilisant la session fournie

        Args:
            db (Session): La session de base de données
            user_id (int): L'ID de l'utilisateur

        Returns:
            Optional[User]: L'utilisateur si trouvé, None sinon
        """
        return self.get(db, user_id)
