from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from epiceventsCRM.models.models import Event, Client, Contract
from epiceventsCRM.dao.base_dao import BaseDAO


class EventDAO(BaseDAO[Event]):
    """
    DAO pour les opérations sur les événements.
    """
    
    def __init__(self):
        """
        Initialise le DAO avec le modèle Event.
        """
        super().__init__(Event)
    
    def get_by_client(self, db: Session, client_id: int) -> List[Event]:
        """
        Récupère tous les événements associés à un client.
        
        Args:
            db (Session): La session de base de données
            client_id (int): L'ID du client
            
        Returns:
            List[Event]: Liste des événements du client
        """
        return list(db.scalars(select(self.model).where(self.model.client_id == client_id)))
    
    def get_by_contract(self, db: Session, contract_id: int) -> List[Event]:
        """
        Récupère tous les événements associés à un contrat.
        
        Args:
            db (Session): La session de base de données
            contract_id (int): L'ID du contrat
            
        Returns:
            List[Event]: Liste des événements du contrat
        """
        return list(db.scalars(select(self.model).where(self.model.contract_id == contract_id)))
    
    def get_by_support(self, db: Session, support_id: int) -> List[Event]:
        """
        Récupère tous les événements assignés à un support.
        
        Args:
            db (Session): La session de base de données
            support_id (int): L'ID du support
            
        Returns:
            List[Event]: Liste des événements assignés au support
        """
        return list(db.scalars(select(self.model).where(self.model.support_contact_id == support_id)))
    
    def get_by_commercial(self, db: Session, commercial_id: int) -> List[Event]:
        """
        Récupère tous les événements des contrats des clients dont un commercial est responsable.
        
        Args:
            db (Session): La session de base de données
            commercial_id (int): L'ID du commercial
            
        Returns:
            List[Event]: Liste des événements liés au commercial
        """
        # Cette méthode nécessite généralement une jointure avec les tables Contract et Client
        # Voici une implémentation simplifiée qui suppose que les relations sont correctement définies
        stmt = select(self.model).join(
            self.model.contract
        ).join(
            self.model.contract.client
        ).where(
            self.model.contract.client.sales_contact_id == commercial_id
        )
        return list(db.scalars(stmt))
    
    def update_support(self, db: Session, event_id: int, support_id: int) -> Optional[Event]:
        """
        Met à jour le support assigné à un événement.
        
        Args:
            db (Session): La session de base de données
            event_id (int): L'ID de l'événement à mettre à jour
            support_id (int): L'ID du nouveau support
            
        Returns:
            Event or None: L'événement mis à jour ou None si non trouvé
        """
        event = self.get(db, event_id)
        if not event:
            return None
        return self.update(db, event, {"support_contact_id": support_id})
    
    def update_notes(self, db: Session, event_id: int, notes: str) -> Optional[Event]:
        """
        Met à jour les notes d'un événement.
        
        Args:
            db (Session): La session de base de données
            event_id (int): L'ID de l'événement à mettre à jour
            notes (str): Les nouvelles notes
            
        Returns:
            Event or None: L'événement mis à jour ou None si non trouvé
        """
        event = self.get(db, event_id)
        if not event:
            return None
        return self.update(db, event, {"notes": notes})

    def assign_support_contact(self, db: Session, event_id: int, support_contact_id: int) -> Optional[Event]:
        """
        Assigne un contact support à un événement existant.
        
        Args:
            db (Session): La session de base de données
            event_id (int): L'ID de l'événement
            support_contact_id (int): L'ID du contact support
            
        Returns:
            Event or None: L'événement mis à jour ou None si non trouvé
        """
        event = self.get(db, event_id)
        if not event:
            return None
            
        return self.update(db, event, {"support_contact_id": support_contact_id})

    def create_event(self, db: Session, event_data: Dict) -> Optional[Event]:
        """
        Crée un nouvel événement avec les informations du client récupérées automatiquement.
        
        Args:
            db (Session): La session de base de données
            event_data (Dict): Les données de l'événement
            
        Returns:
            Optional[Event]: L'événement créé ou None si erreur
        """
        # Récupérer le contrat associé à l'événement pour obtenir le client
        contract_id = event_data.get("contract_id")
        if contract_id is None:
            print("Aucun contract_id fourni dans les données de l'événement")
            return None
        
        # Récupérer le contrat
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            print(f"Contrat avec ID {contract_id} non trouvé dans la base de données")
            return None
        
        # Récupérer le client à partir du contrat
        client_id = contract.client_id
        client = db.query(Client).filter(Client.id == client_id).first()
        if client:
            print(f"Client trouvé: {client.fullname}, Email: {client.email}")
            # Ajouter les informations du client dans l'événement
            event_data["client_id"] = client.id
            event_data["client_name"] = client.fullname
            event_data["client_contact"] = f"Email: {client.email}, Tél: {client.phone_number}"
        else:
            print(f"Client avec ID {client_id} non trouvé dans la base de données")
            # Valeurs par défaut pour éviter les problèmes
            event_data["client_id"] = None
            event_data["client_name"] = "Information non disponible"
            event_data["client_contact"] = "Information non disponible"
        
        # Créer l'événement
        return self.create(db, event_data) 