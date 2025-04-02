from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import update, and_
from datetime import datetime

from epiceventsCRM.models.models import Contract, Client, User
from epiceventsCRM.dao.base_dao import BaseDAO


class ContractDAO(BaseDAO):
    """
    Data Access Object pour les contrats
    """
    
    def __init__(self, session: Session):
        """
        Initialise la classe ContractDAO avec une session DB
        
        Args:
            session: Session SQLAlchemy active
        """
        self.session = session
        self.model = Contract
    
    def create_contract(self, client_id: int, amount: float, sales_contact_id: int, status: bool = False) -> Contract:
        """
        Crée un nouveau contrat
        
        Args:
            client_id: ID du client associé au contrat
            amount: Montant total du contrat
            sales_contact_id: ID du commercial responsable
            status: Statut du contrat (False = non signé, True = signé)
            
        Returns:
            Contract: L'objet contrat créé
        """
        contract = Contract(
            client_id=client_id,
            amount=amount,
            remaining_amount=amount,  # Au départ, montant restant = montant total
            create_date=datetime.now(),
            status=status,
            sales_contact_id=sales_contact_id
        )
        
        self.session.add(contract)
        self.session.commit()
        return contract
    
    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """
        Récupère un contrat par son ID
        
        Args:
            contract_id: ID du contrat à récupérer
            
        Returns:
            Contract or None: Le contrat trouvé ou None
        """
        return self.session.query(Contract).filter(Contract.id == contract_id).first()
    
    def get_all_contracts(self) -> List[Contract]:
        """
        Récupère tous les contrats
        
        Returns:
            List[Contract]: Liste de tous les contrats
        """
        return self.session.query(Contract).all()
    
    def get_contracts_by_client(self, client_id: int) -> List[Contract]:
        """
        Récupère tous les contrats associés à un client
        
        Args:
            client_id: ID du client
            
        Returns:
            List[Contract]: Liste des contrats du client
        """
        return self.session.query(Contract).filter(Contract.client_id == client_id).all()
    
    def get_contracts_by_sales_contact(self, sales_contact_id: int) -> List[Contract]:
        """
        Récupère tous les contrats associés à un commercial
        
        Args:
            sales_contact_id: ID du commercial
            
        Returns:
            List[Contract]: Liste des contrats gérés par le commercial
        """
        return self.session.query(Contract).filter(Contract.sales_contact_id == sales_contact_id).all()
    
    def update_contract(self, contract_id: int, data: Dict) -> Optional[Contract]:
        """
        Met à jour un contrat
        
        Args:
            contract_id: ID du contrat à mettre à jour
            data: Dictionnaire contenant les champs à mettre à jour
            
        Returns:
            Contract or None: Le contrat mis à jour ou None
        """
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            return None
            
        for key, value in data.items():
            if hasattr(contract, key):
                setattr(contract, key, value)
        
        self.session.commit()
        return contract
    
    def update_contract_status(self, contract_id: int, status: bool) -> Optional[Contract]:
        """
        Met à jour le statut d'un contrat
        
        Args:
            contract_id: ID du contrat
            status: Nouveau statut (True = signé, False = non signé)
            
        Returns:
            Contract or None: Le contrat mis à jour ou None
        """
        return self.update_contract(contract_id, {"status": status})
    
    def update_remaining_amount(self, contract_id: int, remaining_amount: float) -> Optional[Contract]:
        """
        Met à jour le montant restant d'un contrat
        
        Args:
            contract_id: ID du contrat
            remaining_amount: Nouveau montant restant
            
        Returns:
            Contract or None: Le contrat mis à jour ou None
        """
        return self.update_contract(contract_id, {"remaining_amount": remaining_amount})
    
    def delete_contract(self, contract_id: int) -> bool:
        """
        Supprime un contrat
        
        Args:
            contract_id: ID du contrat à supprimer
            
        Returns:
            bool: True si supprimé avec succès, False sinon
        """
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            return False
            
        self.session.delete(contract)
        self.session.commit()
        return True 