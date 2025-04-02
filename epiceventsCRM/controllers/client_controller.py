from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.models.models import Client
from epiceventsCRM.controllers.auth_controller import AuthController

class ClientController:
    """
    Contrôleur pour la gestion des clients.
    """
    
    def __init__(self, session: Session = None):
        """
        Initialise le contrôleur avec une session DB optionnelle
        
        Args:
            session (Session, optional): Session SQLAlchemy active
        """
        self.session = session
        self.client_dao = ClientDAO(session)
        self.auth_controller = AuthController()
    
    def check_permission(self, token: str, permission: str) -> bool:
        """
        Vérifie si l'utilisateur a la permission spécifiée.
        
        Args:
            token (str): Le token JWT
            permission (str): La permission à vérifier
            
        Returns:
            bool: True si l'utilisateur a la permission, False sinon
        """
        return self.auth_controller.check_permission(token, permission)
    
    def create_client(self, db: Session, token: str, client_data: Dict) -> Optional[Client]:
        """
        Crée un nouveau client.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_data (Dict): Les données du client
            
        Returns:
            Optional[Client]: Le client créé si la permission est accordée, None sinon
        """
        if not self.check_permission(token, "create_client"):
            return None
            
        # Récupération des informations de l'utilisateur depuis le token
        user_info = self.auth_controller.verify_token(token)
        if not user_info:
            return None
            
        # Attribution du commercial (l'utilisateur connecté) au client
        client_data["sales_contact_id"] = user_info.get("sub")
            
        return self.client_dao.create(db, client_data)
    
    def get_client(self, db: Session, token: str, client_id: int) -> Optional[Client]:
        """
        Récupère un client par son ID.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_id (int): L'ID du client
            
        Returns:
            Optional[Client]: Le client si trouvé et si la permission est accordée, None sinon
        """
        # Tous les utilisateurs peuvent lire les clients
        if not self.check_permission(token, "read_client"):
            return None
            
        return self.client_dao.get(db, client_id)
    
    def get_all_clients(self, db: Session, token: str, skip: int = 0, limit: int = 100) -> List[Client]:
        """
        Récupère tous les clients.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            skip (int): Nombre de clients à sauter
            limit (int): Nombre maximum de clients à retourner
            
        Returns:
            List[Client]: Liste des clients si la permission est accordée, liste vide sinon
        """
        # Tous les utilisateurs peuvent lire les clients
        if not self.check_permission(token, "read_client"):
            return []
            
        return self.client_dao.get_all(db, skip=skip, limit=limit)
    
    def get_my_clients(self, db: Session, token: str) -> List[Client]:
        """
        Récupère tous les clients gérés par l'utilisateur connecté.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            
        Returns:
            List[Client]: Liste des clients gérés par l'utilisateur
        """
        # Vérification des permissions
        if not self.check_permission(token, "read_client"):
            return []
            
        # Récupération des informations de l'utilisateur depuis le token
        user_info = self.auth_controller.verify_token(token)
        if not user_info:
            return []
            
        # Récupération des clients gérés par l'utilisateur
        return self.client_dao.get_by_sales_contact(db, user_info.get("sub"))
    
    def update_client(self, db: Session, token: str, client_id: int, client_data: Dict) -> Optional[Client]:
        """
        Met à jour un client.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_id (int): L'ID du client
            client_data (Dict): Les nouvelles données
            
        Returns:
            Optional[Client]: Le client mis à jour si la permission est accordée, None sinon
        """
        if not self.check_permission(token, "update_client"):
            return None
            
        # Vérification que le client existe
        client = self.client_dao.get(db, client_id)
        if not client:
            return None
            
        # Vérification que l'utilisateur est bien le commercial du client
        user_info = self.auth_controller.verify_token(token)
        if not user_info or (client.sales_contact_id != user_info.get("sub") and 
                             user_info.get("department") != "gestion"):
            return None
            
        return self.client_dao.update(db, client, client_data)
    
    def delete_client(self, db: Session, token: str, client_id: int) -> bool:
        """
        Supprime un client.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_id (int): L'ID du client
            
        Returns:
            bool: True si le client a été supprimé et si la permission est accordée, False sinon
        """
        if not self.check_permission(token, "delete_client"):
            return False
            
        # Vérification que le client existe
        client = self.client_dao.get(db, client_id)
        if not client:
            return False
            
        # Vérification que l'utilisateur est bien le commercial du client
        user_info = self.auth_controller.verify_token(token)
        if not user_info or (client.sales_contact_id != user_info.get("sub") and 
                             user_info.get("department") != "gestion"):
            return False
            
        return self.client_dao.delete(db, client_id)
        
    # Méthodes pour compatibilité avec la vue
    def list_clients(self, token: str) -> tuple:
        """
        Liste tous les clients accessibles par l'utilisateur
        
        Args:
            token: Token JWT de l'utilisateur
            
        Returns:
            tuple: (succès, liste des clients ou message d'erreur)
        """
        if not self.session:
            return False, "Session de base de données non disponible"
            
        try:
            clients = self.get_all_clients(self.session, token)
            return True, clients
        except Exception as e:
            return False, str(e) 