from typing import Generic, List, Optional, Type, TypeVar, Tuple

from sqlalchemy import select, func, Column
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
        self, db: Session, page: int = 1, page_size: int = 10, filters: dict = None
    ) -> Tuple[List[ModelType], int]:
        """
        Récupère toutes les entités avec pagination et filtres optionnels.

        Args:
            db (Session): La session de base de données
            page (int): Numéro de la page (commence à 1)
            page_size (int): Nombre d'éléments par page
            filters (dict, optional): Dictionnaire des filtres à appliquer.
                                      La clé est le nom de l'attribut, la valeur est la valeur attendue
                                      ou un tuple (opérateur, valeur) comme ('gt', 0).

        Returns:
            Tuple[List[ModelType], int]: (Liste des entités, nombre total d'entités filtrées)
        """

        skip = (page - 1) * page_size

        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column: Column = getattr(self.model, key)
                    if value is None:
                        query = query.where(column.is_(None))
                        count_query = count_query.where(column.is_(None))
                    elif isinstance(value, tuple) and len(value) == 2 and value[0] == "gt":
                        # Gérer le filtre 'greater than' (utilisé pour unpaid)
                        query = query.where(column > value[1])
                        count_query = count_query.where(column > value[1])
                    else:
                        query = query.where(column == value)
                        count_query = count_query.where(column == value)
                else:
                    print(
                        f"Avertissement: Attribut de filtre inconnu '{key}' pour le modèle {self.model.__name__}"
                    )

        total = db.scalar(count_query)

        items = list(db.scalars(query.order_by(self.model.id).offset(skip).limit(page_size)))

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
