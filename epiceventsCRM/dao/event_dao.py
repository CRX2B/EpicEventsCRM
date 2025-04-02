from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from epiceventsCRM.models.models import Event
from epiceventsCRM.dao.base_dao import BaseDAO


class EventDAO(BaseDAO):
    """
    DAO pour les opérations sur les événements.
    """
    
    def __init__(self, session: Session):
        """
        Initialise la classe EventDAO avec une session DB
        
        Args:
            session: Session SQLAlchemy active
        """
        self.session = session
        self.model = Event
    
    def create_event(self, 
                    name: str, 
                    contract_id: int, 
                    client_id: int, 
                    start_event: datetime, 
                    end_event: datetime, 
                    location: str, 
                    support_contact_id: Optional[int] = None,
                    attendees: Optional[int] = None,
                    notes: Optional[str] = None) -> Event:
        """
        Crée un nouvel événement
        
        Args:
            name: Nom de l'événement
            contract_id: ID du contrat associé
            client_id: ID du client associé
            start_event: Date et heure de début
            end_event: Date et heure de fin
            location: Lieu de l'événement
            support_contact_id: ID du contact support (optionnel)
            attendees: Nombre de participants (optionnel)
            notes: Notes supplémentaires (optionnel)
            
        Returns:
            Event: L'événement créé
        """
        event = Event(
            name=name,
            contract_id=contract_id,
            client_id=client_id,
            start_event=start_event,
            end_event=end_event,
            location=location,
            support_contact_id=support_contact_id,
            attendees=attendees,
            notes=notes
        )
        
        self.session.add(event)
        self.session.commit()
        return event
    
    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """
        Récupère un événement par son ID
        
        Args:
            event_id: ID de l'événement
            
        Returns:
            Event or None: L'événement trouvé ou None
        """
        return self.session.query(Event).filter(Event.id == event_id).first()
    
    def get_all_events(self) -> List[Event]:
        """
        Récupère tous les événements
        
        Returns:
            List[Event]: Liste de tous les événements
        """
        return self.session.query(Event).all()
    
    def get_events_by_client(self, client_id: int) -> List[Event]:
        """
        Récupère tous les événements associés à un client
        
        Args:
            client_id: ID du client
            
        Returns:
            List[Event]: Liste des événements du client
        """
        return self.session.query(Event).filter(Event.client_id == client_id).all()
    
    def get_events_by_contract(self, contract_id: int) -> List[Event]:
        """
        Récupère tous les événements associés à un contrat
        
        Args:
            contract_id: ID du contrat
            
        Returns:
            List[Event]: Liste des événements du contrat
        """
        return self.session.query(Event).filter(Event.contract_id == contract_id).all()
    
    def get_events_by_support_contact(self, support_contact_id: int) -> List[Event]:
        """
        Récupère tous les événements associés à un contact support
        
        Args:
            support_contact_id: ID du contact support
            
        Returns:
            List[Event]: Liste des événements gérés par le contact support
        """
        return self.session.query(Event).filter(Event.support_contact_id == support_contact_id).all()
    
    def update_event(self, event_id: int, data: Dict) -> Optional[Event]:
        """
        Met à jour un événement
        
        Args:
            event_id: ID de l'événement à mettre à jour
            data: Dictionnaire contenant les champs à mettre à jour
            
        Returns:
            Event or None: L'événement mis à jour ou None
        """
        event = self.get_event_by_id(event_id)
        if not event:
            return None
        
        for key, value in data.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        self.session.commit()
        return event
    
    def assign_support_contact(self, event_id: int, support_contact_id: int) -> Optional[Event]:
        """
        Attribue un contact support à un événement
        
        Args:
            event_id: ID de l'événement
            support_contact_id: ID du contact support
            
        Returns:
            Event or None: L'événement mis à jour ou None
        """
        return self.update_event(event_id, {"support_contact_id": support_contact_id})
    
    def delete_event(self, event_id: int) -> bool:
        """
        Supprime un événement
        
        Args:
            event_id: ID de l'événement à supprimer
            
        Returns:
            bool: True si supprimé avec succès, False sinon
        """
        event = self.get_event_by_id(event_id)
        if not event:
            return False
        
        self.session.delete(event)
        self.session.commit()
        return True 