from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.event_dao import EventDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Event
from epiceventsCRM.utils.permissions import require_permission, PermissionError, Department
from epiceventsCRM.utils.sentry_utils import capture_exception
from epiceventsCRM.utils.auth import verify_token


class EventController(BaseController[Event]):
    """
    Contrôleur pour la gestion des événements.

    Gère les opérations CRUD sur les événements avec des permissions spécifiques :
    - Les commerciaux peuvent voir les événements de leurs clients
    - Le département support a un accès complet
    """

    def __init__(self):
        """Initialise le contrôleur des événements avec le DAO approprié."""
        super().__init__(EventDAO(), "event")
        self.contract_dao = ContractDAO()
        self.client_dao = ClientDAO()
        self.user_dao = UserDAO()

    @require_permission("read_{entity_name}")
    def get_event(self, token: str, db: Session, event_id: int) -> Optional[Event]:
        """
        Récupère un événement par son ID.

        Args:
            token: Token JWT de l'utilisateur (utilisé par le décorateur)
            db: Session de base de données
            event_id: ID de l'événement à récupérer

        Returns:
            L'événement si trouvé, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """

        # Récupérer l'événement avec ses relations
        event = self.dao.get(db, event_id)
        if not event:
            return None

        return event

    @require_permission("read_{entity_name}")
    def get_events_by_contract(self, token: str, db: Session, contract_id: int) -> List[Event]:
        """
        Liste les événements liés à un contrat.

        Args:
            token: Token JWT de l'utilisateur (utilisé par le décorateur)
            db: Session de base de données
            contract_id: ID du contrat

        Returns:
            Liste des événements liés au contrat

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """

        return self.dao.get_by_contract(db, contract_id)

    @require_permission("read_{entity_name}")
    def get_events_by_support(self, token: str, db: Session) -> List[Event]:
        """
        Liste les événements assignés au support connecté.

        Args:
            token: Token JWT de l'utilisateur (utilisé par le décorateur et pour l'ID)
            db: Session de base de données

        Returns:
            Liste d'événements (peut être vide)

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        # La permission de base est gérée par le décorateur
        payload = verify_token(token)  # Nécessaire ici pour obtenir l'ID utilisateur
        if not payload or "sub" not in payload:
            return []

        user_id = payload["sub"]
        events = self.dao.get_by_support(db, user_id)
        return events  # Retourne directement la liste

    @require_permission("create_event")
    @capture_exception
    def create(self, token: str, db: Session, event_data: Dict) -> Optional[Event]:
        """
        Crée un nouvel événement.

        Args:
            token: Token JWT de l'utilisateur (utilisé par le décorateur)
            db: Session de base de données
            event_data: Données de l'événement à créer

        Returns:
            L'événement créé si succès, None sinon.

        Raises:
            ValueError: Si des champs obligatoires sont manquants ou si contrat non trouvé.
            PermissionError: Si l'utilisateur n'a pas la permission de création (via décorateur).
            IntegrityError: Si une contrainte de base de données est violée.
        """
        required_fields = ["name", "contract_id", "start_event", "end_event", "location"]
        for field in required_fields:
            if field not in event_data:
                raise ValueError(f"Champ obligatoire manquant: {field}")

        contract = self.contract_dao.get(db, event_data["contract_id"])
        if not contract:
            raise ValueError(f"Contrat avec ID {event_data['contract_id']} non trouvé")

        # S'assurer que le contrat est signé AVANT de créer un événement (vérifier APRES avoir trouvé le contrat)
        if not contract.status:
            raise ValueError(
                f"Le contrat {contract.id} n'est pas signé. Impossible de créer un événement."
            )

        try:
            event = self.dao.create_event(db, event_data)
            return event
        except IntegrityError as e:
            db.rollback()  # Annuler la transaction en cas d'erreur d'intégrité
            capture_exception(e)
            # Renvoyer une erreur spécifique ou None
            raise IntegrityError(
                f"Erreur de base de données lors de la création: {e}", orig=e, params=event_data
            )
        except Exception as e:
            db.rollback()
            capture_exception(e)
            # Renvoyer None ou relancer une exception générique
            raise

    @require_permission("update_{entity_name}")
    def update_event_support(
        self, token: str, db: Session, event_id: int, support_id: int
    ) -> Optional[Event]:
        """
        Met à jour le contact support d'un événement.
        Réservé au département gestion.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            event_id: ID de l'événement
            support_id: ID du contact support

        Returns:
            L'événement mis à jour si autorisé, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de mise à jour
        """
        # Vérifier que l'événement existe
        event = self.dao.get(db, event_id)
        if not event:
            return None

        # Vérifier que le support existe
        support = self.user_dao.get(db, support_id)
        if not support:
            return None

        # Vérifier que le support appartient bien au département support
        payload = verify_token(token)
        if not payload or payload.get("department") != "gestion":
            return None

        # Mise à jour du support
        return self.dao.update_support(db, event_id, support_id)

    @require_permission("update_{entity_name}")
    @capture_exception
    def update_event_notes(
        self, token: str, db: Session, event_id: int, notes: str
    ) -> Optional[Event]:
        """
        Met à jour les notes d'un événement.
        Réservé au support assigné à l'événement.

        Args:
            token: Token JWT de l'utilisateur (utilisé par le décorateur et pour vérification)
            db: Session de base de données
            event_id: ID de l'événement
            notes: Nouvelles notes

        Returns:
            L'événement mis à jour si succès, None si non trouvé ou non autorisé.

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de base (via décorateur)
                         ou n'est pas le support assigné.
        """

        # Récupérer l'événement
        event = self.dao.get(db, event_id)
        if not event:
            return None

        # Vérifier le token et la permission spécifique (être le support assigné)
        payload = verify_token(token)
        if not payload or "sub" not in payload:
            raise PermissionError("Token invalide pour la mise à jour des notes.")

        user_id = payload["sub"]
        if event.support_contact_id != user_id:
            # Lever une exception si l'utilisateur n'est pas le bon support
            raise PermissionError(
                f"Vous n'êtes pas le support assigné à cet événement.",
                user_id=user_id,
                permission="update_event_notes",
            )

        try:
            updated_event = self.dao.update_notes(db, event_id, notes)
            return updated_event
        except Exception as e:
            db.rollback()
            capture_exception(e)
            # Renvoyer None ou relancer
            raise

    @require_permission("delete_{entity_name}")
    @capture_exception
    def delete_event(self, token: str, db: Session, event_id: int) -> bool:
        """
        Supprime un événement.
        Réservé au département gestion (vérifié par le décorateur).

        Args:
            token: Token JWT de l'utilisateur (utilisé par le décorateur)
            db: Session de base de données
            event_id: ID de l'événement à supprimer

        Returns:
            True si supprimé, False sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de suppression (via décorateur)
        """

        try:
            return self.dao.delete(db, event_id)
        except Exception as e:
            # Capturer les exceptions potentielles du DAO
            capture_exception(e)
            return False
