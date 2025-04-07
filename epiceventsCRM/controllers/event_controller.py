from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from epiceventsCRM.dao.event_dao import EventDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Event, User, Department
from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.token_manager import decode_token


class EventController(BaseController[Event]):
    """
    Contrôleur pour la gestion des événements.
    Accessible aux départements commercial, support et gestion selon les opérations.
    """
    
    def __init__(self):
        """
        Initialise le contrôleur des événements avec le DAO approprié.
        """
        super().__init__(EventDAO(), "event")
        self.contract_dao = ContractDAO()
        self.client_dao = ClientDAO()
        self.user_dao = UserDAO()

    @require_permission("read_{entity_name}")
    def get_event(self, token: str, db: Session, event_id: int) -> Optional[Event]:
        """
        Récupère un événement par son ID
        
        Args:
            token: Token JWT de l'utilisateur connecté
            db: Session de base de données
            event_id: ID de l'événement à récupérer
            
        Returns:
            Optional[Event]: L'événement si trouvé, None sinon
        """
        # Vérifier que le token est valide
        payload = decode_token(token)
        if not payload:
            return None
            
        # Récupérer l'événement
        return self.dao.get(db, event_id)

    @require_permission("read_{entity_name}")
    def get_events_by_contract(self, token: str, db: Session, contract_id: int) -> List[Event]:
        """
        Liste les événements liés à un contrat
        
        Args:
            token: Token JWT de l'utilisateur connecté
            db: Session de base de données
            contract_id: ID du contrat
            
        Returns:
            List[Event]: Liste des événements liés au contrat
        """
        # Vérifier que le token est valide
        payload = decode_token(token)
        if not payload:
            return []
            
        return self.dao.get_by_contract(db, contract_id)
    
    @require_permission("read_{entity_name}")
    def get_events_by_commercial(self, token: str, db: Session, commercial_id: int) -> List[Event]:
        """
        Liste les événements liés à un commercial
        
        Args:
            token: Token JWT de l'utilisateur connecté
            db: Session de base de données
            commercial_id: ID du commercial
            
        Returns:
            List[Event]: Liste des événements liés au commercial
        """
        # Vérifier que le token est valide
        payload = decode_token(token)
        if not payload:
            return []
            
        return self.dao.get_by_commercial(db, commercial_id)
    
    @require_permission("read_{entity_name}")
    def get_events_by_support(self, token: str, db: Session) -> List[Event]:
        """
        Liste les événements assignés au support connecté
        
        Args:
            token: Token JWT de l'utilisateur connecté
            db: Session de base de données
            
        Returns:
            List[Event]: Liste des événements assignés au support
        """
        # Récupérer l'ID de l'utilisateur depuis le token
        payload = decode_token(token)
        if not payload or "user_id" not in payload:
            return []
            
        user_id = payload["user_id"]
        return self.dao.get_by_support(db, user_id)

    @require_permission("create_{entity_name}")
    def create_event(self, token: str, db: Session, event_data: Dict) -> Optional[Event]:
        """
        Crée un nouvel événement.
        
        Args:
            token: Le token JWT
            db: La session de base de données
            event_data: Les données de l'événement
            
        Returns:
            Optional[Event]: L'événement créé si autorisé, None sinon
        """
        print("=== CRÉATION D'ÉVÉNEMENT ===")
        print("Event data reçue:", event_data)
        
        # Vérification des données requises
        required_keys = ["name", "contract_id", "start_event", "end_event", "location"]
        missing_keys = [key for key in required_keys if key not in event_data]
        
        print("Clés manquantes:", missing_keys if missing_keys else "Aucune")
        
        if missing_keys:
            print("Données requises manquantes:", missing_keys)
            return None
        
        # Vérification que le contrat existe
        contract_id = event_data.get("contract_id")
        print("Recherche du contrat:", contract_id)
        contract = self.contract_dao.get(db, contract_id)
        
        print("Contrat trouvé:", contract is not None)
        
        if not contract:
            print("Contrat non trouvé")
            return None
        
        # Obtention de l'ID de l'utilisateur depuis le token
        print("Décodage du token:", token)
        payload = decode_token(token)
        print("Payload:", payload)
        
        if not payload or "user_id" not in payload:
            print("Token invalide ou user_id manquant")
            return None
        
        # Ajout de l'ID du client à partir du contrat
        event_data["client_id"] = contract.client_id
        
        # Création de l'événement avec les informations du client
        print("Création de l'événement avec les infos client...")
        event = self.dao.create_event(db, event_data)
        print("Événement créé:", event)
        return event

    @require_permission("update_{entity_name}")
    def update_event_support(self, token: str, db: Session, event_id: int, support_id: int) -> Optional[Event]:
        """
        Met à jour le contact support d'un événement.
        Réservé au département gestion.
        
        Args:
            token: Token JWT de l'utilisateur connecté
            db: Session de base de données
            event_id: ID de l'événement
            support_id: ID du contact support
            
        Returns:
            Optional[Event]: L'événement mis à jour si autorisé, None sinon
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
    def update_event_notes(self, token: str, db: Session, event_id: int, notes: str) -> Optional[Event]:
        """
        Met à jour les notes d'un événement.
        Réservé au support assigné à l'événement.
        
        Args:
            token: Token JWT de l'utilisateur connecté
            db: Session de base de données
            event_id: ID de l'événement
            notes: Nouvelles notes
            
        Returns:
            Optional[Event]: L'événement mis à jour si autorisé, None sinon
        """
        # Récupérer l'événement
        event = self.dao.get(db, event_id)
        if not event:
            return None
            
        # Vérifier que l'utilisateur est bien le support assigné
        payload = decode_token(token)
        if not payload or "user_id" not in payload:
            return None
            
        user_id = payload["user_id"]
        if event.support_contact_id != user_id:
            return None
            
        # Mise à jour des notes
        return self.dao.update_notes(db, event_id, notes)

    @require_permission("delete_{entity_name}")
    def delete_event(self, token: str, db: Session, event_id: int) -> bool:
        """
        Supprime un événement.
        Réservé au département gestion.
        
        Args:
            token: Token JWT de l'utilisateur connecté
            db: Session de base de données
            event_id: ID de l'événement à supprimer
            
        Returns:
            bool: True si supprimé, False sinon
        """
        # Vérifier que l'utilisateur est du département gestion
        payload = decode_token(token)
        if not payload or payload.get("department") != "gestion":
            return False
            
        # Suppression de l'événement
        return self.dao.delete(db, event_id) 