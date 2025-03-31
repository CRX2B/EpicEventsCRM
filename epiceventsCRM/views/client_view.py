from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.models.models import Client

class ClientView:
    """
    Vue pour les opérations sur les clients.
    """
    
    def __init__(self):
        self.client_controller = ClientController()
    
    def display_client(self, client: Client) -> Dict:
        """
        Affiche les informations d'un client.
        
        Args:
            client (Client): Le client à afficher
            
        Returns:
            Dict: Les informations du client formatées
        """
        if not client:
            return {"error": "Client non trouvé."}
            
        return {
            "id": client.id,
            "fullname": client.fullname,
            "email": client.email,
            "phone_number": client.phone_number,
            "enterprise": client.enterprise,
            "create_date": client.create_date.strftime("%Y-%m-%d %H:%M:%S") if client.create_date else None,
            "update_date": client.update_date.strftime("%Y-%m-%d %H:%M:%S") if client.update_date else None,
            "sales_contact_id": client.sales_contact_id,
            "sales_contact": client.sales_contact.fullname if client.sales_contact else None
        }
    
    def display_clients(self, clients: List[Client]) -> List[Dict]:
        """
        Affiche une liste de clients.
        
        Args:
            clients (List[Client]): La liste des clients à afficher
            
        Returns:
            List[Dict]: Les informations des clients formatées
        """
        return [self.display_client(client) for client in clients]
    
    def create_client(self, db: Session, token: str, client_data: Dict) -> Dict:
        """
        Crée un nouveau client.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_data (Dict): Les données du client
            
        Returns:
            Dict: Les informations du client créé ou un message d'erreur
        """
        # Vérification des données obligatoires
        required_fields = ["fullname", "email", "phone_number", "enterprise"]
        for field in required_fields:
            if field not in client_data:
                return {"error": f"Le champ '{field}' est obligatoire."}
        
        # Création du client
        client = self.client_controller.create_client(db, token, client_data)
        if not client:
            return {"error": "Vous n'avez pas la permission de créer un client ou le token est invalide."}
            
        return {
            "message": "Client créé avec succès.",
            "client": self.display_client(client)
        }
    
    def get_client(self, db: Session, token: str, client_id: int) -> Dict:
        """
        Récupère un client par son ID.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_id (int): L'ID du client
            
        Returns:
            Dict: Les informations du client ou un message d'erreur
        """
        client = self.client_controller.get_client(db, token, client_id)
        if not client:
            return {"error": "Client non trouvé ou vous n'avez pas la permission d'accéder à ce client."}
            
        return {
            "client": self.display_client(client)
        }
    
    def get_all_clients(self, db: Session, token: str, skip: int = 0, limit: int = 100) -> Dict:
        """
        Récupère tous les clients.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            skip (int): Nombre de clients à sauter
            limit (int): Nombre maximum de clients à retourner
            
        Returns:
            Dict: La liste des clients ou un message d'erreur
        """
        clients = self.client_controller.get_all_clients(db, token, skip, limit)
        if not clients:
            return {"message": "Aucun client trouvé ou vous n'avez pas la permission d'accéder aux clients."}
            
        return {
            "clients": self.display_clients(clients),
            "count": len(clients)
        }
    
    def get_my_clients(self, db: Session, token: str) -> Dict:
        """
        Récupère tous les clients gérés par l'utilisateur connecté.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            
        Returns:
            Dict: La liste des clients ou un message d'erreur
        """
        clients = self.client_controller.get_my_clients(db, token)
        if not clients:
            return {"message": "Aucun client trouvé ou vous n'avez pas la permission d'accéder aux clients."}
            
        return {
            "clients": self.display_clients(clients),
            "count": len(clients)
        }
    
    def update_client(self, db: Session, token: str, client_id: int, client_data: Dict) -> Dict:
        """
        Met à jour un client.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_id (int): L'ID du client
            client_data (Dict): Les nouvelles données
            
        Returns:
            Dict: Les informations du client mis à jour ou un message d'erreur
        """
        client = self.client_controller.update_client(db, token, client_id, client_data)
        if not client:
            return {"error": "Client non trouvé, vous n'avez pas la permission de mettre à jour ce client ou le token est invalide."}
            
        return {
            "message": "Client mis à jour avec succès.",
            "client": self.display_client(client)
        }
    
    def delete_client(self, db: Session, token: str, client_id: int) -> Dict:
        """
        Supprime un client.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_id (int): L'ID du client
            
        Returns:
            Dict: Un message de succès ou d'erreur
        """
        success = self.client_controller.delete_client(db, token, client_id)
        if not success:
            return {"error": "Client non trouvé, vous n'avez pas la permission de supprimer ce client ou le token est invalide."}
            
        return {
            "message": "Client supprimé avec succès."
        } 