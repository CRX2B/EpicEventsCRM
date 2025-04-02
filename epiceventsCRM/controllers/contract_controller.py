from typing import List, Dict, Optional, Tuple, Any, Union
from sqlalchemy.orm import Session
import jwt
from datetime import datetime

from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Contract, User, Department


class ContractController:
    """
    Contrôleur pour gérer les contrats
    """
    
    def __init__(self, session: Session):
        """
        Initialise le contrôleur avec une session DB
        
        Args:
            session: Session SQLAlchemy active
        """
        self.session = session
        self.contract_dao = ContractDAO(session)
        self.client_dao = ClientDAO(session)
        self.user_dao = UserDAO(session)
    
    def create_contract(self, token: str, client_id: int, amount: float, sales_contact_id: Optional[int] = None) -> Tuple[bool, Union[Contract, str]]:
        """
        Crée un nouveau contrat
        
        Args:
            token: Token JWT de l'utilisateur connecté
            client_id: ID du client associé au contrat
            amount: Montant total du contrat
            sales_contact_id: ID du commercial responsable (optionnel)
            
        Returns:
            Tuple[bool, Union[Contract, str]]: (succès, contrat ou message d'erreur)
        """
        try:
            # Vérifier l'authentification et les autorisations
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Vérifier si l'utilisateur est dans le département gestion
            department_name = user.department.departement_name.lower()
            if department_name != "gestion":
                return False, "Accès refusé: seul le département gestion peut créer des contrats"
            
            # Vérifier si le client existe
            client = self.client_dao.get_client_by_id(client_id)
            if not client:
                return False, f"Client avec ID {client_id} non trouvé"
            
            # Si sales_contact_id n'est pas fourni, utiliser le commercial du client
            if sales_contact_id is None:
                # Utiliser le commercial du client
                sales_contact_id = client.sales_contact_id
            
            # Vérifier si le commercial existe et est bien dans le département commercial
            sales_contact = self.user_dao.get_user_by_id(sales_contact_id)
            if not sales_contact:
                return False, f"Commercial avec ID {sales_contact_id} non trouvé"
                
            if sales_contact.department.departement_name.lower() != "commercial":
                return False, "Le contact commercial doit être du département commercial"
            
            # Créer le contrat
            contract = self.contract_dao.create_contract(
                client_id=client_id,
                amount=amount,
                sales_contact_id=sales_contact_id
            )
            
            return True, contract
            
        except Exception as e:
            return False, f"Erreur lors de la création du contrat: {str(e)}"
    
    def get_contract(self, token: str, contract_id: int) -> Tuple[bool, Union[Contract, str]]:
        """
        Récupère un contrat par son ID
        
        Args:
            token: Token JWT de l'utilisateur connecté
            contract_id: ID du contrat à récupérer
            
        Returns:
            Tuple[bool, Union[Contract, str]]: (succès, contrat ou message d'erreur)
        """
        try:
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Récupérer le contrat
            contract = self.contract_dao.get_contract_by_id(contract_id)
            if not contract:
                return False, f"Contrat avec ID {contract_id} non trouvé"
            
            # Tous les collaborateurs peuvent lire tous les contrats
            return True, contract
                
        except Exception as e:
            return False, f"Erreur lors de la récupération du contrat: {str(e)}"
    
    def list_contracts(self, token: str) -> Tuple[bool, Union[List[Contract], str]]:
        """
        Liste tous les contrats accessibles par l'utilisateur
        
        Args:
            token: Token JWT de l'utilisateur connecté
            
        Returns:
            Tuple[bool, Union[List[Contract], str]]: (succès, liste de contrats ou message d'erreur)
        """
        try:
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Tous les collaborateurs peuvent lire tous les contrats
            contracts = self.contract_dao.get_all_contracts()
            return True, contracts
            
        except Exception as e:
            return False, f"Erreur lors de la récupération des contrats: {str(e)}"
    
    def update_contract(self, token: str, contract_id: int, update_data: Dict) -> Tuple[bool, Union[Contract, str]]:
        """
        Met à jour un contrat existant
        
        Args:
            token: Token JWT de l'utilisateur connecté
            contract_id: ID du contrat à mettre à jour
            update_data: Nouvelles données du contrat
            
        Returns:
            Tuple[bool, Union[Contract, str]]: (succès, contrat mis à jour ou message d'erreur)
        """
        try:
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Récupérer le contrat
            contract = self.contract_dao.get_contract_by_id(contract_id)
            if not contract:
                return False, f"Contrat avec ID {contract_id} non trouvé"
                
            # Vérifier les permissions selon le département
            department_name = user.department.departement_name.lower()
            
            if department_name == "gestion":
                # La gestion peut mettre à jour tous les contrats
                pass
            elif department_name == "commercial":
                # Les commerciaux peuvent mettre à jour uniquement leurs contrats
                client = self.client_dao.get_client_by_id(contract.client_id)
                if not client or client.sales_contact_id != user_id:
                    return False, "Accès refusé: ce contrat n'est pas lié à vos clients"
            else:
                return False, "Accès refusé: vous n'avez pas la permission de mettre à jour les contrats"
            
            # Mettre à jour le contrat
            updated_contract = self.contract_dao.update_contract(contract_id, update_data)
            return True, updated_contract
            
        except Exception as e:
            return False, f"Erreur lors de la mise à jour du contrat: {str(e)}"
    
    def delete_contract(self, token: str, contract_id: int) -> Tuple[bool, str]:
        """
        Supprime un contrat
        
        Args:
            token: Token JWT de l'utilisateur connecté
            contract_id: ID du contrat à supprimer
            
        Returns:
            Tuple[bool, str]: (succès, message de confirmation ou d'erreur)
        """
        try:
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Seule la gestion peut supprimer des contrats
            department_name = user.department.departement_name.lower()
            if department_name != "gestion":
                return False, "Accès refusé: seule la gestion peut supprimer des contrats"
            
            # Récupérer le contrat
            contract = self.contract_dao.get_contract_by_id(contract_id)
            if not contract:
                return False, f"Contrat avec ID {contract_id} non trouvé"
            
            # Supprimer le contrat
            success = self.contract_dao.delete_contract(contract_id)
            if not success:
                return False, "Échec de la suppression du contrat"
                
            return True, f"Contrat avec ID {contract_id} supprimé avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de la suppression du contrat: {str(e)}" 