from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import User
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.sentry_utils import capture_exception, capture_message


class UserController(BaseController[User]):
    """
    Contrôleur pour la gestion des utilisateurs.
    
    Gère les opérations CRUD sur les utilisateurs avec des permissions spécifiques :
    - Les utilisateurs peuvent voir et modifier leurs propres informations
    - Le département gestion a un accès complet
    """

    def __init__(self):
        """Initialise le contrôleur des utilisateurs avec le DAO approprié."""
        super().__init__(UserDAO(), "user")

    @require_permission("read_user")
    def get_user(self, token: str, db: Session, user_id: int) -> Optional[User]:
        """
        Récupère un utilisateur par son ID.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_id: ID de l'utilisateur à récupérer

        Returns:
            L'utilisateur si trouvé, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        return self.dao.get_by_id(db, user_id)

    @require_permission("read_user")
    def get_all_users(self, token: str, db: Session) -> List[User]:
        """
        Récupère tous les utilisateurs.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données

        Returns:
            Liste de tous les utilisateurs

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        return self.get_all(token, db)[0]

    @require_permission("create_user")
    def create(self, token: str, db: Session, user_data: Dict) -> Optional[User]:
        """
        Crée un nouvel utilisateur.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_data: Données de l'utilisateur à créer

        Returns:
            L'utilisateur créé si l'opération réussit, None sinon

        Raises:
            ValueError: Si des champs obligatoires sont manquants
            PermissionError: Si l'utilisateur n'a pas la permission de création
        """
        user = self.dao.create(db, user_data)
        if user:
            # Journalisation Sentry de la création d'un collaborateur
            capture_message(
                f"Création d'un collaborateur: {user.email}",
                level="info",
                extra={"user_id": user.id, "email": user.email},
            )
        return user

    @require_permission("update_user")
    @capture_exception
    def update(self, token: str, db: Session, user_id: int, user_data: Dict) -> Optional[User]:
        """
        Met à jour un utilisateur.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_id: ID de l'utilisateur à mettre à jour
            user_data: Nouvelles données de l'utilisateur

        Returns:
            L'utilisateur mis à jour si l'opération réussit, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de mise à jour
        """
        user = super().update(token, db, user_id, user_data)
        if user:
            # Journalisation Sentry de la modification d'un collaborateur
            capture_message(
                f"Modification d'un collaborateur: {user.email}",
                level="info",
                extra={
                    "user_id": user.id,
                    "email": user.email,
                    "updated_fields": list(user_data.keys()),
                },
            )
        return user

    @require_permission("delete_user")
    def delete(self, token: str, db: Session, user_id: int) -> bool:
        """
        Supprime un utilisateur.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_id: ID de l'utilisateur à supprimer

        Returns:
            True si supprimé, False sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de suppression
        """
        return self.dao.delete(db, user_id)

    @require_permission("read_user")
    def get_users_by_department(self, token: str, db: Session, department_id: int) -> List[User]:
        """
        Récupère tous les utilisateurs d'un département.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            department_id: ID du département

        Returns:
            Liste des utilisateurs du département

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        users, _ = self.get_all(token, db)
        return [user for user in users if user.departement_id == department_id]

    @require_permission("update_user")
    def update_user_department(
        self, token: str, db: Session, user_id: int, department_id: int
    ) -> Optional[User]:
        """
        Met à jour le département d'un utilisateur.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_id: ID de l'utilisateur
            department_id: ID du nouveau département

        Returns:
            L'utilisateur mis à jour si l'opération réussit, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de mise à jour
        """
        user = self.dao.update_department(db, user_id, department_id)
        if user:
            # Journalisation Sentry de la modification du département
            capture_message(
                f"Modification du département pour: {user.email}",
                level="info",
                extra={"user_id": user.id, "email": user.email, "department_id": department_id},
            )
        return user

    def authenticate(self, db: Session, email: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur avec son email et son mot de passe.

        Args:
            db: Session de base de données
            email: Email de l'utilisateur
            password: Mot de passe de l'utilisateur

        Returns:
            L'utilisateur authentifié si les identifiants sont valides, None sinon
        """
        return self.dao.authenticate(db, email, password)

    @require_permission("read_user")
    def get_by_email(self, token: str, db: Session, email: str) -> Optional[User]:
        """
        Récupère un utilisateur par son email.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            email: Email de l'utilisateur

        Returns:
            L'utilisateur si trouvé, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        return self.dao.get_by_email(db, email)

    @require_permission("create_user")
    @capture_exception
    def create_with_department(
        self, token: str, db: Session, user_data: Dict, department_id: int
    ) -> Optional[User]:
        """
        Crée un utilisateur avec un département spécifique.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_data: Données de l'utilisateur
            department_id: ID du département

        Returns:
            L'utilisateur créé si l'opération réussit, None sinon

        Raises:
            ValueError: Si des champs obligatoires sont manquants
            PermissionError: Si l'utilisateur n'a pas la permission de création
        """
        user_data["departement_id"] = department_id
        return self.create(token, db, user_data)

    @require_permission("update_user")
    @capture_exception
    def update_password(
        self, token: str, db: Session, user_id: int, new_password: str
    ) -> Optional[User]:
        """
        Met à jour le mot de passe d'un utilisateur.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_id: ID de l'utilisateur
            new_password: Nouveau mot de passe

        Returns:
            L'utilisateur mis à jour si l'opération réussit, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de mise à jour
        """
        return self.dao.update_password(db, user_id, new_password)
