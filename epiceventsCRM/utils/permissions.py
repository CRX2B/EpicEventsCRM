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
        "create_client",
        "read_client",
        "update_client",
        "delete_client",
        "create_contract",
        "read_contract",
        "update_contract"
    },
    Department.SUPPORT: {
        "read_client",
        "read_contract",
        "create_event",
        "read_event",
        "update_event"
    },
    Department.GESTION: {
        # Gestion des utilisateurs
        "create_user",
        "read_user",
        "update_user",
        "delete_user",
        # Gestion des contrats
        "create_contract",
        "read_contract",
        "update_contract",
        # Gestion des événements
        "read_event",
        "update_event"  # Pour attribuer un support à l'événement
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