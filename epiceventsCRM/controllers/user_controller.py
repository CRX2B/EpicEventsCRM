from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import User
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.sentry_utils import capture_exception, capture_message
from epiceventsCRM.utils.validators import is_valid_email_format


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

    @require_permission("update_user")
    @capture_exception
    def update(self, token: str, db: Session, user_id: int, user_data: Dict) -> Optional[User]:
        """
        Met à jour un utilisateur.
        Avec validation des formats pour email et phone_number.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_id: ID de l'utilisateur à mettre à jour
            user_data: Nouvelles données de l'utilisateur

        Returns:
            L'utilisateur mis à jour si l'opération réussit, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de mise à jour
            ValueError: If email format is invalid.
        """
        # --- Validation ---
        errors = []
        if "email" in user_data:
            email = user_data["email"]
            if not email or not is_valid_email_format(email):
                errors.append("Format d'email invalide.")

        if "fullname" in user_data and len(user_data["fullname"]) > 100:
            errors.append("Nom complet trop long (max 100 caractères).")

        if errors:
            error_message = (
                f"Erreurs de validation lors de la mise à jour de l'utilisateur {user_id}: "
                + ", ".join(errors)
            )
            capture_message(error_message, level="warning")
            raise ValueError(error_message)
        # --- Fin Validation ---

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

        user = self.dao.get(db, user_id)
        if not user:
            return False
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
    def update_user_department_via_update(
        self, token: str, db: Session, user_id: int, department_id: int
    ) -> Optional[User]:
        """
        Met à jour le département d'un utilisateur en utilisant la méthode update standard.

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

        user = self.update(token, db, user_id, {"departement_id": department_id})
        if user:
            # Journalisation Sentry de la modification du département
            capture_message(
                f"Modification du département pour: {user.email}",
                level="info",
                extra={"user_id": user.id, "email": user.email, "department_id": department_id},
            )
        return user

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
        Avec validation des formats pour email et phone_number.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            user_data: Données de l'utilisateur
            department_id: ID du département

        Returns:
            L'utilisateur créé si l'opération réussit, None sinon

        Raises:
            ValueError: Si le département ID est invalide, si des champs sont manquants, ou format email invalide
            PermissionError: Si l'utilisateur n'a pas la permission de création
        """

        user_data["departement_id"] = department_id

        # --- Validation ---
        errors = []
        required_fields = ["fullname", "email", "password"]
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                errors.append(f"Champ obligatoire manquant ou vide: {field}")

        email = user_data.get("email")
        if email and not is_valid_email_format(email):
            errors.append("Format d'email invalide.")

        if user_data.get("fullname") and len(user_data["fullname"]) > 100:
            errors.append("Nom complet trop long (max 100 caractères).")

        if errors:
            error_message = (
                "Erreurs de validation lors de la création de l'utilisateur (avec département): "
                + ", ".join(errors)
            )
            capture_message(error_message, level="warning")
            raise ValueError(error_message)
        # --- Fin Validation ---

        try:
            user = self.dao.create(db, user_data)
        except IntegrityError as e:
            if db:
                db.rollback()
            capture_exception(e)
            if (
                "violates foreign key constraint" in str(e).lower()
                and "departments" in str(e).lower()
            ):
                raise ValueError(f"Département ID {department_id} invalide.")
            else:
                raise ValueError(f"Contrainte de base de données violée lors de la création: {e}")
        except Exception as e:
            if db:
                db.rollback()
            capture_exception(e)
            raise

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
