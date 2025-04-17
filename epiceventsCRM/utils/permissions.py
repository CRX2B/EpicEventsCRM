from enum import Enum
from functools import wraps
from typing import Callable, Set

from epiceventsCRM.utils.sentry_utils import capture_message


class Department(str, Enum):
    """Énumération des départements."""

    COMMERCIAL = "commercial"
    SUPPORT = "support"
    GESTION = "gestion"


# Permissions communes à tous les départements
COMMON_PERMISSIONS = {"read_client", "read_contract", "read_event"}

# Définition des permissions par département
DEPARTMENT_PERMISSIONS = {
    Department.COMMERCIAL: {
        # Permissions spécifiques au département commercial
        "create_client",
        "update_client",
        "delete_client",
        "update_contract",  # Uniquement pour les contrats de ses clients
        "create_event",
        "update_event",
        # Permissions communes
        *COMMON_PERMISSIONS,
    },
    Department.SUPPORT: {
        # Permissions spécifiques au département support
        "update_event",  # Uniquement pour les événements dont ils sont responsables
        # Permissions communes
        *COMMON_PERMISSIONS,
    },
    Department.GESTION: {
        # Permissions spécifiques au département gestion
        "create_user",
        "read_user",
        "update_user",
        "delete_user",
        "create_contract",
        "update_contract",
        "delete_contract",
        "update_event",  # Pour attribuer un support
        "delete_event",
        # Permissions communes
        *COMMON_PERMISSIONS,
    },
}


def get_department_permissions(department: Department) -> Set[str]:
    """
    Récupère les permissions d'un département.

    Args:
        department (Department): Le département

    Returns:
        Set[str]: L'ensemble des permissions
    """
    return DEPARTMENT_PERMISSIONS.get(department, set())


def has_permission(department: Department, permission: str) -> bool:
    """
    Vérifie si un département a une permission.

    Args:
        department (Department): Le département
        permission (str): La permission à vérifier

    Returns:
        bool: True si le département a la permission, False sinon
    """
    return permission in get_department_permissions(department)


class PermissionError(Exception):
    """Exception levée lorsqu'une permission est refusée."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.message = message
        self.user_id = kwargs.get("user_id")
        self.permission = kwargs.get("permission")


def require_permission(permission_template: str):
    """
    Décorateur qui vérifie si l'utilisateur a la permission requise.

    Args:
        permission_template (str): Le modèle de permission, peut contenir {entity_name}
                                  qui sera remplacé par la valeur de self.entity_name

    Returns:
        Callable: La fonction décorée

    Raises:
        PermissionError: Si l'utilisateur n'a pas la permission requise
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Formatter la permission si nécessaire
            permission = permission_template
            if "{entity_name}" in permission_template and hasattr(self, "entity_name"):
                permission = permission_template.format(entity_name=self.entity_name)

            # Récupérer le token - Vérifie args[0] ou args[1] ou kwargs
            token = None
            if len(args) >= 1 and isinstance(args[0], str):
                token = args[0]
            elif len(args) >= 2 and isinstance(args[1], str):
                token = args[1]
            elif "token" in kwargs:
                token = kwargs["token"]

            if not token:
                raise PermissionError("Token manquant", permission=permission)

            # Si pas de vérification d'autorisation dans la classe, lever une exception
            if not hasattr(self, "auth_controller"):
                raise PermissionError(
                    "Contrôleur d'authentification manquant", permission=permission
                )

            # Vérifier la permission
            if not self.auth_controller.check_permission(token, permission):
                payload = self.auth_controller.verify_token(token)
                user_id = payload.get("sub") if payload else None
                raise PermissionError(
                    f"Permission refusée: {permission}", user_id=user_id, permission=permission
                )

            return func(self, *args, **kwargs)

        return wrapper

    return decorator
