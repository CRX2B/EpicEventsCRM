from typing import List, Optional, Dict, TypeVar, Generic, Type
from sqlalchemy.orm import Session
from epiceventsCRM.dao.base_dao import BaseDAO
from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.utils.permissions import require_permission

T = TypeVar('T')

class BaseController(Generic[T]):
    """
    Contrôleur de base qui fournit des fonctionnalités CRUD génériques.
    """
    
    def __init__(self, dao: BaseDAO, entity_name: str):
        """
        Initialise le contrôleur avec un DAO et un nom d'entité.
        
        Args:
            dao (BaseDAO): L'objet DAO pour accéder aux données
            entity_name (str): Le nom de l'entité (utilisé pour construire les noms de permissions)
        """
        self.dao = dao
        self.entity_name = entity_name
        self.auth_controller = AuthController()
    
    @require_permission("read_{entity_name}")
    def get(self, token: str, db: Session, entity_id: int) -> Optional[T]:
        """
        Récupère une entité par son ID.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            entity_id (int): L'ID de l'entité
            
        Returns:
            Optional[T]: L'entité si trouvée, None sinon
        """
        return self.dao.get(db, entity_id)
    
    @require_permission("read_{entity_name}")
    def get_all(self, token: str, db: Session, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Récupère toutes les entités.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            skip (int): Nombre d'entités à sauter
            limit (int): Nombre maximum d'entités à retourner
            
        Returns:
            List[T]: Liste des entités
        """
        return self.dao.get_all(db, skip=skip, limit=limit)
    
    @require_permission("create_{entity_name}")
    def create(self, token: str, db: Session, data: Dict) -> Optional[T]:
        """
        Crée une nouvelle entité.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            data (Dict): Les données de l'entité
            
        Returns:
            Optional[T]: L'entité créée
        """
        return self.dao.create(db, data)
    
    @require_permission("update_{entity_name}")
    def update(self, token: str, db: Session, entity_id: int, data: Dict) -> Optional[T]:
        """
        Met à jour une entité.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            entity_id (int): L'ID de l'entité
            data (Dict): Les nouvelles données
            
        Returns:
            Optional[T]: L'entité mise à jour si trouvée, None sinon
        """
        entity = self.dao.get(db, entity_id)
        if not entity:
            return None
        return self.dao.update(db, entity, data)
    
    @require_permission("delete_{entity_name}")
    def delete(self, token: str, db: Session, entity_id: int) -> bool:
        """
        Supprime une entité.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            entity_id (int): L'ID de l'entité
            
        Returns:
            bool: True si l'entité a été supprimée, False sinon
        """
        return self.dao.delete(db, entity_id)
    
    def format_permission(self, action: str) -> str:
        """
        Formate une permission en utilisant l'action et le nom de l'entité.
        
        Args:
            action (str): L'action (create, read, update, delete)
            
        Returns:
            str: La permission formatée
        """
        return f"{action}_{self.entity_name}" 