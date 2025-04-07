from enum import Enum
from typing import List, Set, Callable, Any
from functools import wraps

class Department(str, Enum):
    """Énumération des départements."""
    COMMERCIAL = "commercial"
    SUPPORT = "support"
    GESTION = "gestion"

# Permissions communes à tous les départements
COMMON_PERMISSIONS = {
    "read_client",
    "read_contract",
    "read_event"
}

# Définition des permissions par département
DEPARTMENT_PERMISSIONS = {
    Department.COMMERCIAL: {
        # Permissions spécifiques au département commercial
        "create_client",
        "update_client",
        "delete_client",
        "update_contract",  # Uniquement pour les contrats de ses clients
        "create_event",
        # Permissions communes
        *COMMON_PERMISSIONS
    },
    Department.SUPPORT: {
        # Permissions spécifiques au département support
        "update_event",  # Uniquement pour les événements dont ils sont responsables
        # Permissions communes
        *COMMON_PERMISSIONS
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
        "delete_event",  # Permission pour supprimer un événement
        # Permissions communes
        *COMMON_PERMISSIONS
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

def require_permission(permission_template: str):
    """
    Décorateur qui vérifie si l'utilisateur a la permission requise.
    
    Args:
        permission_template (str): Le modèle de permission, peut contenir {entity_name}
                                  qui sera remplacé par la valeur de self.entity_name

    Returns:
        Callable: La fonction décorée si la permission est accordée, None sinon
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Formatter la permission si nécessaire
            permission = permission_template
            if "{entity_name}" in permission_template and hasattr(self, "entity_name"):
                permission = permission_template.format(entity_name=self.entity_name)
            
            # Récupérer le token - généralement le premier ou le deuxième argument après self
            token = None
            if len(args) >= 1 and isinstance(args[0], str):
                token = args[0]
            elif 'token' in kwargs:
                token = kwargs['token']
                
            # Si pas de vérification d'autorisation dans la classe, retourner None
            if not hasattr(self, 'auth_controller'):
                return None
            
            # Vérifier la permission
            if not self.auth_controller.check_permission(token, permission):
                return None
                
            return func(self, *args, **kwargs)
        return wrapper
    return decorator 