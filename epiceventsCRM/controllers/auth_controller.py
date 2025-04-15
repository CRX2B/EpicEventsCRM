from typing import Dict, Optional

from sqlalchemy.orm import Session

from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.utils.auth import generate_token, verify_token
from epiceventsCRM.utils.permissions import Department, has_permission
from epiceventsCRM.utils.sentry_utils import capture_exception, capture_message, set_user_context


class AuthController:
    """
    Contrôleur pour la gestion de l'authentification et des tokens JWT.
    
    Gère les opérations liées à l'authentification :
    - Génération de tokens JWT
    - Vérification de tokens
    - Gestion des permissions
    """

    def __init__(self):
        """Initialise le contrôleur d'authentification avec le DAO approprié."""
        self.user_dao = UserDAO()

    @capture_exception
    def login(self, db: Session, email: str, password: str) -> Optional[Dict]:
        """
        Authentifie un utilisateur et génère un token JWT.

        Args:
            db: Session de base de données
            email: Email de l'utilisateur
            password: Mot de passe de l'utilisateur

        Returns:
            Dictionnaire contenant les informations de l'utilisateur et le token si authentifié, None sinon

        Raises:
            ValueError: Si les identifiants sont invalides
        """
        user = self.user_dao.authenticate(db, email, password)
        if not user:
            capture_message(f"Échec de connexion pour l'email: {email}", level="warning")
            return None

        # Récupération du nom du département
        department_name = user.department.departement_name if user.department else None
        if not department_name:
            capture_message(f"Utilisateur sans département: {email}", level="error")
            return None

        # Génération du token
        token = generate_token(user.id, department_name)

        # Définir le contexte utilisateur pour Sentry
        set_user_context(user_id=user.id, email=user.email, username=user.fullname)
        capture_message(f"Connexion réussie pour: {email}", level="info")

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "fullname": user.fullname,
                "department": department_name,
            },
            "token": token,
        }

    @capture_exception
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Vérifie la validité d'un token JWT.

        Args:
            token: Token JWT à vérifier

        Returns:
            Payload du token si valide, None sinon

        Raises:
            JWTError: Si le token est invalide ou expiré
        """
        return verify_token(token)

    @capture_exception
    def check_permission(self, token: str, permission: str) -> bool:
        """
        Vérifie si un utilisateur a une permission spécifique.

        Args:
            token: Token JWT de l'utilisateur
            permission: Permission à vérifier

        Returns:
            True si l'utilisateur a la permission, False sinon

        Raises:
            JWTError: Si le token est invalide ou expiré
            ValueError: Si le département n'est pas valide
        """
        payload = self.verify_token(token)
        if not payload:
            capture_message("Vérification de permission avec un token invalide", level="warning")
            return False

        # Récupération du département depuis le token
        try:
            department = Department(payload["department"])
            has_perm = has_permission(department, permission)

            if not has_perm:
                user_id = payload.get("sub")
                capture_message(
                    f"Accès refusé: utilisateur {user_id} a tenté d'accéder à {permission}",
                    level="warning",
                    extra={
                        "user_id": user_id,
                        "department": department.value,
                        "permission": permission,
                    },
                )
            return has_perm
        except ValueError as e:
            capture_message(
                f"Département invalide dans le token: {payload.get('department')}",
                level="error",
                extra={"error": str(e)},
            )
            return False
