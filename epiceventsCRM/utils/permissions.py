from enum import Enum
from typing import List, Set

class Department(str, Enum):
    """Énumération des départements."""
    COMMERCIAL = "commercial"
    SUPPORT = "support"
    GESTION = "gestion"

# Définition des permissions par département
DEPARTMENT_PERMISSIONS = {
    Department.COMMERCIAL: {
        # Permissions spécifiques au département commercial
        "create_client",
        "update_client",
        "delete_client",
        "update_contract",  # Uniquement pour les contrats de ses clients
        "create_event",
        # Permissions de lecture communes
        "read_client",
        "read_contract",
        "read_event",
        "read_user"
    },
    Department.SUPPORT: {
        # Permissions spécifiques au département support
        "update_event",  # Uniquement pour les événements dont ils sont responsables
        # Permissions de lecture communes
        "read_client",
        "read_contract",
        "read_event",
        "read_user"
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
        # Permissions de lecture communes
        "read_client",
        "read_contract",
        "read_event"
    }
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