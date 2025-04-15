from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.event_dao import EventDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Event
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.token_manager import decode_token


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
            token: Token JWT de l'utilisateur
            db: Session de base de données
            event_id: ID de l'événement à récupérer

        Returns:
            L'événement si trouvé, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        # Vérifier que le token est valide
        payload = decode_token(token)
        if not payload:
            return None

        # Récupérer l'événement avec ses relations
        event = self.dao.get(db, event_id)
        if not event:
            return None

        # Charger les relations nécessaires
        db.refresh(event)
        return event

    @require_permission("read_{entity_name}")
    def get_events_by_contract(self, token: str, db: Session, contract_id: int) -> List[Event]:
        """
        Liste les événements liés à un contrat.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            contract_id: ID du contrat

        Returns:
            Liste des événements liés au contrat

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        # Vérifier que le token est valide
        payload = decode_token(token)
        if not payload:
            return []

        return self.dao.get_by_contract(db, contract_id)

    @require_permission("read_{entity_name}")
    def get_events_by_commercial(self, token: str, db: Session, commercial_id: int) -> List[Event]:
        """
        Liste les événements liés à un commercial.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            commercial_id: ID du commercial

        Returns:
            Liste des événements liés au commercial

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        # Vérifier que le token est valide
        payload = decode_token(token)
        if not payload:
            return []

        return self.dao.get_by_commercial(db, commercial_id)

    @require_permission("read_{entity_name}")
    def get_events_by_support(self, token: str, db: Session) -> List[Event]:
        """
        Liste les événements assignés au support connecté.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données

        Returns:
            Liste des événements assignés au support

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        # Récupérer l'ID de l'utilisateur depuis le token
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            print("Erreur: payload invalide ou 'sub' manquant")
            return []

        user_id = payload["sub"]
        return self.dao.get_by_support(db, user_id)

    @require_permission("create_event")
    def create(self, token: str, db: Session, event_data: Dict) -> Optional[Event]:
        """
        Crée un nouvel événement.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            event_data: Données de l'événement à créer

        Returns:
            L'événement créé si l'opération réussit, None sinon

        Raises:
            ValueError: Si des champs obligatoires sont manquants
            PermissionError: Si l'utilisateur n'a pas la permission de création
        """
        try:
            # Vérification des champs obligatoires
            required_fields = ["name", "contract_id", "start_event", "end_event", "location"]
            for field in required_fields:
                if field not in event_data:
                    print(f"Erreur: champ obligatoire manquant: {field}")
                    return None

            # Vérification que le contrat existe
            contract = self.contract_dao.get(db, event_data["contract_id"])
            if not contract:
                print(f"Erreur: contrat avec ID {event_data['contract_id']} non trouvé")
                return None

            # Création de l'événement
            event = self.dao.create_event(db, event_data)
            if not event:
                print("Erreur: création de l'événement échouée")
                return None

            return event
        except Exception as e:
            print(f"Erreur lors de la création de l'événement: {str(e)}")
            return None

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
        payload = decode_token(token)
        if not payload or payload.get("department") != "gestion":
            return None

        # Mise à jour du support
        return self.dao.update_support(db, event_id, support_id)

    @require_permission("update_{entity_name}")
    def update_event_notes(
        self, token: str, db: Session, event_id: int, notes: str
    ) -> Optional[Event]:
        """
        Met à jour les notes d'un événement.
        Réservé au support assigné à l'événement.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            event_id: ID de l'événement
            notes: Nouvelles notes

        Returns:
            L'événement mis à jour si autorisé, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de mise à jour
        """
        # Récupérer l'événement
        event = self.dao.get(db, event_id)
        if not event:
            return None

        # Vérifier que l'utilisateur est bien le support assigné
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            print("Erreur: payload invalide ou 'sub' manquant")
            return None

        user_id = payload["sub"]
        if event.support_contact_id != user_id:
            print(f"Erreur: l'utilisateur {user_id} n'est pas le support de l'événement")
            return None

        # Mise à jour des notes
        return self.dao.update_notes(db, event_id, notes)

    @require_permission("delete_{entity_name}")
    def delete_event(self, token: str, db: Session, event_id: int) -> bool:
        """
        Supprime un événement.
        Réservé au département gestion.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            event_id: ID de l'événement à supprimer

        Returns:
            True si supprimé, False sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de suppression
        """
        # Vérifier que l'utilisateur est du département gestion
        payload = decode_token(token)
        if not payload or payload.get("department") != "gestion":
            return False

        # Suppression de l'événement
        return self.dao.delete(db, event_id)
