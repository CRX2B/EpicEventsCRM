from typing import Generic, List, Optional, Type, TypeVar, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import Session


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

    def get_all(
        self, db: Session, page: int = 1, page_size: int = 10
    ) -> Tuple[List[ModelType], int]:
        """
        Récupère toutes les entités avec pagination basée sur les pages.

        Args:
            db (Session): La session de base de données
            page (int): Numéro de la page (commence à 1)
            page_size (int): Nombre d'éléments par page

        Returns:
            Tuple[List[ModelType], int]: (Liste des entités, nombre total d'entités)
        """
        # Calcul du skip
        skip = (page - 1) * page_size

        # Récupération du nombre total d'éléments
        total = db.scalar(select(func.count()).select_from(self.model))

        # Récupération des éléments paginés
        items = list(db.scalars(select(self.model).offset(skip).limit(page_size)))

        return items, total

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
