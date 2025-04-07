from typing import List, Dict, Optional, Tuple, Any, Union
from sqlalchemy.orm import Session
import jwt
from datetime import datetime

from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Contract, User, Department, Client
from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.token_manager import decode_token


class ContractController(BaseController[Contract]):
    """
    Contrôleur pour la gestion des contrats.
    Accessible principalement aux départements commercial et gestion.
    """
    
    def __init__(self):
        """
        Initialise le contrôleur des contrats avec le DAO approprié.
        """
        super().__init__(ContractDAO(), "contract")
        self.client_dao = ClientDAO()
        self.user_dao = UserDAO()
        
        # Alias pour la compatibilité avec les tests
        self.list_contracts = self.get_all
        self.get_contract = self.get
        self.update_contract = self.update
    
    def create_contract(self, token: str, client_id: int, amount: float, status: bool = False) -> Tuple[bool, Union[Contract, str]]:
        """
        Crée un nouveau contrat
        
        Args:
            token: Token JWT de l'utilisateur connecté
            client_id: ID du client associé au contrat
            amount: Montant total du contrat
            status: Statut du contrat (False = non signé, True = signé)
            
        Returns:
            Tuple[bool, Union[Contract, str]]: (succès, contrat ou message d'erreur)
        """
        # Obtention de la session de base de données depuis la méthode
        from epiceventsCRM.database import get_session
        db = get_session()
        
        try:
            # Vérifier l'authentification et les autorisations
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Récupérer l'ID de l'utilisateur depuis le token 
            # (selon le format du token, la clé peut être 'user_id' ou 'sub')
            user_id = payload.get('user_id') or payload.get('sub')
            
            if not user_id:
                return False, "Token invalide: ID utilisateur manquant"
                
            # Obtenez l'utilisateur à partir de l'ID
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, f"Utilisateur avec ID {user_id} non trouvé"
                
            # Vérifier si l'utilisateur est dans le département gestion
            department_name = user.department.departement_name.lower()
            if department_name != "gestion":
                return False, "Accès refusé: seul le département gestion peut créer des contrats"
            
            # Vérifier si le client existe
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return False, f"Client avec ID {client_id} non trouvé"
            
            # Utiliser le commercial du client
            sales_contact_id = client.sales_contact_id
            
            # Vérifier si le commercial existe et est bien dans le département commercial
            sales_contact = db.query(User).filter(User.id == sales_contact_id).first()
            if not sales_contact:
                return False, f"Commercial avec ID {sales_contact_id} non trouvé"
                
            if sales_contact.department.departement_name.lower() != "commercial":
                return False, "Le contact commercial doit être du département commercial"
            
            # Créer le contrat
            contract_data = {
                "client_id": client_id,
                "amount": amount,
                "remaining_amount": amount,  # Au départ, montant restant = montant total
                "create_date": datetime.now(),
                "status": status,
                "sales_contact_id": sales_contact_id
            }
            
            # Créer le contrat dans la base de données
            contract = Contract(**contract_data)
            db.add(contract)
            db.commit()
            db.refresh(contract)
            
            return True, contract
        
        except Exception as e:
            db.rollback()
            return False, f"Erreur lors de la création du contrat: {str(e)}"
        finally:
            db.close()
    
    @require_permission("read_contract")
    def get_contracts_by_client(self, token: str, db: Session, client_id: int) -> List[Contract]:
        """
        Récupère tous les contrats d'un client.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            client_id (int): L'ID du client
            
        Returns:
            List[Contract]: Liste des contrats du client
        """
        return self.dao.get_by_client(db, client_id)
    
    @require_permission("read_contract")
    def get_contracts_by_commercial(self, token: str, db: Session) -> List[Contract]:
        """
        Récupère tous les contrats gérés par un commercial.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            
        Returns:
            List[Contract]: Liste des contrats du commercial
        """
        # Récupérer l'ID de l'utilisateur depuis le token
        payload = decode_token(token)
        if not payload or "user_id" not in payload:
            return []
        
        user_id = payload["user_id"]
        return self.dao.get_by_commercial(db, user_id)
    
    @require_permission("update_contract")
    def update_contract_status(self, token: str, db: Session, contract_id: int, status: bool) -> Optional[Contract]:
        """
        Met à jour le statut d'un contrat (signé ou non).
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            contract_id (int): L'ID du contrat
            status (bool): Le nouveau statut
            
        Returns:
            Optional[Contract]: Le contrat mis à jour si trouvé, None sinon
        """
        contract = self.dao.get(db, contract_id)
        if not contract:
            return None
        
        # Vérifier si le commercial actuel est l'utilisateur qui fait la requête
        payload = decode_token(token)
        if not payload or "user_id" not in payload or "department" not in payload:
            return None
        
        user_id = payload["user_id"]
        department = payload["department"]
        
        # Si c'est un commercial, il ne peut modifier que les contrats liés à ses clients
        if department == "commercial" and contract.client.commercial_contact_id != user_id:
            return None
        
        # Mise à jour du statut
        return self.dao.update_status(db, contract, status)
    
    @require_permission("update_contract")
    def update_contract_amount(self, token: str, db: Session, contract_id: int, amount: float) -> Optional[Contract]:
        """
        Met à jour le montant d'un contrat.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            contract_id (int): L'ID du contrat
            amount (float): Le nouveau montant
            
        Returns:
            Optional[Contract]: Le contrat mis à jour si trouvé, None sinon
        """
        contract = self.dao.get(db, contract_id)
        if not contract:
            return None
        
        # Vérifier si le commercial actuel est l'utilisateur qui fait la requête
        payload = decode_token(token)
        if not payload or "user_id" not in payload or "department" not in payload:
            return None
        
        user_id = payload["user_id"]
        department = payload["department"]
        
        # Si c'est un commercial, il ne peut modifier que les contrats liés à ses clients
        if department == "commercial" and contract.client.commercial_contact_id != user_id:
            return None
        
        # Mise à jour du montant
        return self.dao.update_amount(db, contract, amount)
    
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
            contract = self.dao.get_contract_by_id(contract_id)
            if not contract:
                return False, f"Contrat avec ID {contract_id} non trouvé"
            
            # Supprimer le contrat
            success = self.dao.delete_contract(contract_id)
            if not success:
                return False, "Échec de la suppression du contrat"
                
            return True, f"Contrat avec ID {contract_id} supprimé avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de la suppression du contrat: {str(e)}" 