from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from epiceventsCRM.models.models import Base

ModelType = TypeVar("ModelType")

class BaseDAO(Generic[ModelType]):
    """
    Classe de base pour les DAO (Data Access Objects).
    Implémente les opérations CRUD de base.
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialise le DAO avec le modèle spécifié.
        
        Args:
            model (Type[ModelType]): Le modèle SQLAlchemy à utiliser
        """
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Récupère une entité par son ID.
        
        Args:
            db (Session): La session de base de données
            id (int): L'ID de l'entité
            
        Returns:
            Optional[ModelType]: L'entité si trouvée, None sinon
        """
        return db.get(self.model, id)
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Récupère toutes les entités avec pagination.
        
        Args:
            db (Session): La session de base de données
            skip (int): Nombre d'entités à sauter
            limit (int): Nombre maximum d'entités à retourner
            
        Returns:
            List[ModelType]: Liste des entités
        """
        return list(db.scalars(select(self.model).offset(skip).limit(limit)))
    
    def create(self, db: Session, obj_in: dict) -> ModelType:
        """
        Crée une nouvelle entité.
        
        Args:
            db (Session): La session de base de données
            obj_in (dict): Les données de l'entité à créer
            
        Returns:
            ModelType: L'entité créée
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        """
        Met à jour une entité existante.
        
        Args:
            db (Session): La session de base de données
            db_obj (ModelType): L'entité à mettre à jour
            obj_in (dict): Les nouvelles données
            
        Returns:
            ModelType: L'entité mise à jour
        """
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: int) -> bool:
        """
        Supprime une entité par son ID.
        
        Args:
            db (Session): La session de base de données
            id (int): L'ID de l'entité à supprimer
            
        Returns:
            bool: True si l'entité a été supprimée, False sinon
        """
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False 