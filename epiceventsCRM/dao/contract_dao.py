from typing import List, Optional, Dict, Type
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_
from datetime import datetime

from epiceventsCRM.models.models import Contract, Client, User
from epiceventsCRM.dao.base_dao import BaseDAO


class ContractDAO(BaseDAO[Contract]):
    """
    Data Access Object pour les contrats
    """
    
    def __init__(self):
        """
        Initialise la classe ContractDAO avec le modèle Contract
        """
        super().__init__(Contract)
    
    def create_contract(self, db: Session, client_id: int, amount: float, sales_contact_id: int, status: bool = False) -> Contract:
        """
        Crée un nouveau contrat
        
        Args:
            db: Session SQLAlchemy active
            client_id: ID du client associé au contrat
            amount: Montant total du contrat
            sales_contact_id: ID du commercial responsable
            status: Statut du contrat (False = non signé, True = signé)
            
        Returns:
            Contract: L'objet contrat créé
        """
        contract_data = {
            "client_id": client_id,
            "amount": amount,
            "remaining_amount": amount,  # Au départ, montant restant = montant total
            "create_date": datetime.now(),
            "status": status,
            "sales_contact_id": sales_contact_id
        }
        
        return self.create(db, contract_data)
    
    def get_by_client(self, db: Session, client_id: int) -> List[Contract]:
        """
        Récupère tous les contrats associés à un client
        
        Args:
            db: Session SQLAlchemy active
            client_id: ID du client
            
        Returns:
            List[Contract]: Liste des contrats du client
        """
        return list(db.scalars(select(Contract).where(Contract.client_id == client_id)))
    
    def get_by_sales_contact(self, db: Session, sales_contact_id: int) -> List[Contract]:
        """
        Récupère tous les contrats associés à un commercial
        
        Args:
            db: Session SQLAlchemy active
            sales_contact_id: ID du commercial
            
        Returns:
            List[Contract]: Liste des contrats gérés par le commercial
        """
        return list(db.scalars(select(Contract).where(Contract.sales_contact_id == sales_contact_id)))
    
    def update_status(self, db: Session, contract_id: int, status: bool) -> Optional[Contract]:
        """
        Met à jour le statut d'un contrat
        
        Args:
            db: Session SQLAlchemy active
            contract_id: ID du contrat
            status: Nouveau statut (True = signé, False = non signé)
            
        Returns:
            Contract or None: Le contrat mis à jour ou None
        """
        contract = self.get(db, contract_id)
        if not contract:
            return None
            
        return self.update(db, contract, {"status": status})
    
    def update_remaining_amount(self, db: Session, contract_id: int, remaining_amount: float) -> Optional[Contract]:
        """
        Met à jour le montant restant d'un contrat
        
        Args:
            db: Session SQLAlchemy active
            contract_id: ID du contrat
            remaining_amount: Nouveau montant restant
            
        Returns:
            Contract or None: Le contrat mis à jour ou None
        """
        contract = self.get(db, contract_id)
        if not contract:
            return None
            
        return self.update(db, contract, {"remaining_amount": remaining_amount})
    
    def delete_contract(self, db: Session, contract_id: int) -> bool:
        """
        Supprime un contrat
        
        Args:
            db: Session SQLAlchemy active
            contract_id: ID du contrat à supprimer
            
        Returns:
            bool: True si supprimé avec succès, False sinon
        """
        return self.delete(db, contract_id) 