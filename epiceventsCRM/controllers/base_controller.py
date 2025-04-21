from typing import Dict, Generic, List, Optional, TypeVar, Tuple

from sqlalchemy.orm import Session

from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.dao.base_dao import BaseDAO
from epiceventsCRM.utils.permissions import PermissionError, require_permission
from epiceventsCRM.utils.sentry_utils import capture_exception, capture_message

T = TypeVar("T")


class BaseController(Generic[T]):
    """
    Contrôleur de base pour les opérations CRUD.

    Cette classe abstraite fournit les fonctionnalités de base pour la gestion des entités :
    - Création
    - Lecture
    - Mise à jour
    - Suppression

    Les classes dérivées doivent implémenter des méthodes spécifiques pour chaque entité.
    """

    def __init__(self, dao: BaseDAO[T], entity_name: str):
        """
        Initialise le contrôleur avec le DAO approprié.

        Args:
            dao: DAO spécifique à l'entité
            entity_name: Nom de l'entité gérée
        """
        self.dao = dao
        self.entity_name = entity_name
        self.auth_controller = AuthController()

    @require_permission("read_{entity_name}")
    @capture_exception
    def get(self, token: str, db: Session, entity_id: int) -> Optional[T]:
        """
        Récupère une entité par son ID.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            entity_id: ID de l'entité à récupérer

        Returns:
            L'entité si trouvée, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        try:
            return self.dao.get(db, entity_id)
        except PermissionError as e:
            capture_message(
                f"Erreur de permission lors de la lecture de {self.entity_name} {entity_id}",
                level="warning",
                extra={"error": str(e)},
            )
            raise

    @require_permission("read_{entity_name}")
    @capture_exception
    def get_all(
        self, token: str, db: Session, page: int = 1, page_size: int = 10, filters: dict = None
    ) -> Tuple[List[T], int]:
        """
        Récupère toutes les entités avec pagination et filtres optionnels.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            page: Numéro de la page (commence à 1)
            page_size: Nombre d'éléments par page
            filters (dict, optional): Dictionnaire des filtres à passer au DAO.

        Returns:
            Tuple[List[T], int]: (Liste des entités, nombre total d'entités filtrées)

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        try:
            return self.dao.get_all(db, page=page, page_size=page_size, filters=filters)
        except PermissionError as e:
            capture_message(
                f"Erreur de permission lors de la lecture de tous les {self.entity_name}s",
                level="warning",
                extra={"error": str(e)},
            )
            raise
        except Exception as e:
            capture_exception(e)
            raise

    @require_permission("create_{entity_name}")
    @capture_exception
    def create(self, token: str, db: Session, data: Dict) -> Optional[T]:
        """
        Crée une nouvelle entité.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            data: Données de l'entité à créer

        Returns:
            L'entité créée si l'opération réussit, None sinon

        Raises:
            ValueError: Si des champs obligatoires sont manquants
            PermissionError: Si l'utilisateur n'a pas la permission de création
        """
        try:
            return self.dao.create(db, data)
        except PermissionError as e:
            capture_message(
                f"Erreur de permission lors de la création d'un {self.entity_name}",
                level="warning",
                extra={"error": str(e)},
            )
            raise

    @require_permission("update_{entity_name}")
    @capture_exception
    def update(self, token: str, db: Session, entity_id: int, data: Dict) -> Optional[T]:
        """
        Met à jour une entité.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            entity_id: ID de l'entité à mettre à jour
            data: Nouvelles données de l'entité

        Returns:
            L'entité mise à jour si l'opération réussit, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de mise à jour
        """
        try:
            entity = self.dao.get(db, entity_id)
            if not entity:
                return None
            updated_entity = self.dao.update(db, entity, data)
            return updated_entity
        except PermissionError as e:
            capture_message(
                f"Erreur de permission lors de la mise à jour du {self.entity_name} {entity_id}",
                level="warning",
                extra={"error": str(e)},
            )
            raise

    @require_permission("delete_{entity_name}")
    @capture_exception
    def delete(self, token: str, db: Session, entity_id: int) -> bool:
        """
        Supprime une entité.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            entity_id: ID de l'entité à supprimer

        Returns:
            True si supprimée, False sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de suppression
        """
        try:
            return self.dao.delete(db, entity_id)
        except PermissionError as e:
            capture_message(
                f"Erreur de permission lors de la suppression du {self.entity_name} {entity_id}",
                level="warning",
                extra={"error": str(e)},
            )
            raise
