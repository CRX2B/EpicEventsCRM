from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.models.models import Client
from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.token_manager import decode_token

class ClientController(BaseController[Client]):
    """
    Contrôleur pour la gestion des clients.
    Accessible principalement au département commercial.
    """
    
    def __init__(self):
        """
        Initialise le contrôleur des clients avec le DAO approprié.
        """
        super().__init__(ClientDAO(), "client")
    
    @require_permission("read_client")
    def get_clients_by_commercial(self, token: str, db: Session) -> List[Client]:
        """
        Récupère tous les clients d'un commercial.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            
        Returns:
            List[Client]: Liste des clients du commercial
        """
        # Récupérer l'ID de l'utilisateur depuis le token
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            return []
        
        user_id = payload["sub"]
        return self.dao.get_by_sales_contact(db, user_id)
    
    @require_permission("update_client")
    def update_client_commercial(self, token: str, db: Session, client_id: int, commercial_id: int) -> Optional[Client]:
        """
        Met à jour le commercial d'un client.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            client_id (int): L'ID du client
            commercial_id (int): L'ID du nouveau commercial
            
        Returns:
            Optional[Client]: Le client mis à jour si trouvé, None sinon
        """
        client = self.dao.get(db, client_id)
        if not client:
            return None
        
        # Vérifier si le commercial actuel est l'utilisateur qui fait la requête (pour les commerciaux)
        payload = decode_token(token)
        if not payload or "sub" not in payload or "department" not in payload:
            return None
        
        user_id = payload["sub"]
        department = payload["department"]
        
        # Si c'est un commercial, il ne peut modifier que ses propres clients
        if department == "commercial" and client.commercial_contact_id != user_id:
            return None
        
        # Mise à jour du commercial
        return self.dao.update_commercial(db, client, commercial_id)

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
    
    @require_permission("create_client")
    def create(self, token: str, db: Session, client_data: Dict) -> Optional[Client]:
        """
        Crée un nouveau client en assignant automatiquement le commercial.
        
        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            client_data (Dict): Les données du client
            
        Returns:
            Optional[Client]: Le client créé
        """
        # Récupération des informations de l'utilisateur depuis le token
        payload = decode_token(token)
        
        if not payload or "sub" not in payload:
            print("Erreur: payload invalide ou 'sub' (user_id) manquant")
            return None
            
        # Attribution du commercial (l'utilisateur connecté) au client
        client_data["sales_contact_id"] = payload["sub"]
            
        # Appeler la méthode create_client du DAO qui définit les dates automatiquement
        try:
            return self.dao.create_client(db, client_data)
        except Exception as e:
            print(f"Erreur lors de la création du client: {str(e)}")
            return None
    
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
            
        return self.dao.get(db, client_id)
    
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
            
        return self.dao.get_all(db, skip=skip, limit=limit)
    
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
        if not user_info or "sub" not in user_info:
            return []
            
        # Récupération des clients gérés par l'utilisateur
        return self.dao.get_by_sales_contact(db, user_info["sub"])
    
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
        client = self.dao.get(db, client_id)
        if not client:
            return None
            
        # Vérification que l'utilisateur est bien le commercial du client
        user_info = self.auth_controller.verify_token(token)
        if not user_info or "sub" not in user_info or (client.sales_contact_id != user_info["sub"] and 
                             user_info.get("department") != "gestion"):
            return None
            
        return self.dao.update_client(db, client_id, client_data)
    
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
        client = self.dao.get(db, client_id)
        if not client:
            return False
            
        # Vérification que l'utilisateur est bien le commercial du client
        user_info = self.auth_controller.verify_token(token)
        if not user_info or "sub" not in user_info or (client.sales_contact_id != user_info["sub"] and 
                             user_info.get("department") != "gestion"):
            return False
            
        return self.dao.delete(db, client_id)
        
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