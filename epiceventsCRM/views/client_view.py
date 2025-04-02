from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import click
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
        
    @staticmethod
    def register_commands(cli_group, get_session, get_token):
        """
        Enregistre les commandes CLI pour la gestion des clients
        
        Args:
            cli_group: Groupe de commandes Click
            get_session: Fonction pour obtenir une session DB
            get_token: Fonction pour obtenir le token JWT
        """
        
        @cli_group.group()
        def client():
            """Gestion des clients"""
            pass
        
        @client.command("list")
        def list_clients():
            """Liste tous les clients accessibles"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour accéder aux clients.")
                return
            client_view = ClientView()
            result = client_view.get_all_clients(session, token)
            if "error" in result:
                click.echo(f"Erreur: {result['error']}")
            elif "clients" in result:
                click.echo(f"Clients ({result['count']} trouvés):")
                for client_info in result["clients"]:
                    click.echo("-" * 50)
                    click.echo(f"ID: {client_info['id']}")
                    click.echo(f"Nom: {client_info['fullname']}")
                    click.echo(f"Email: {client_info['email']}")
                    click.echo(f"Téléphone: {client_info['phone_number']}")
                    click.echo(f"Entreprise: {client_info['enterprise']}")
                    click.echo(f"Commercial: {client_info['sales_contact']}")
                    click.echo("-" * 50)
            else:
                click.echo(result["message"])
        
        @client.command("get")
        @click.argument("client_id", type=int)
        def get_client(client_id):
            """Affiche les détails d'un client spécifique"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour accéder aux clients.")
                return
            client_view = ClientView()
            result = client_view.get_client(session, token, client_id)
            if "error" in result:
                click.echo(f"Erreur: {result['error']}")
            else:
                client_info = result["client"]
                click.echo("-" * 50)
                click.echo(f"ID: {client_info['id']}")
                click.echo(f"Nom: {client_info['fullname']}")
                click.echo(f"Email: {client_info['email']}")
                click.echo(f"Téléphone: {client_info['phone_number']}")
                click.echo(f"Entreprise: {client_info['enterprise']}")
                click.echo(f"Date de création: {client_info['create_date']}")
                click.echo(f"Date de mise à jour: {client_info['update_date']}")
                click.echo(f"Commercial ID: {client_info['sales_contact_id']}")
                click.echo(f"Commercial: {client_info['sales_contact']}")
                click.echo("-" * 50)
        
        @client.command("create")
        def create_client():
            """Crée un nouveau client"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour créer un client.")
                return
            
            # Collecter les données du client
            fullname = click.prompt("Nom complet")
            email = click.prompt("Email")
            phone_number = click.prompt("Numéro de téléphone", type=int)
            enterprise = click.prompt("Entreprise")
            
            client_data = {
                "fullname": fullname,
                "email": email,
                "phone_number": phone_number,
                "enterprise": enterprise
            }
            
            client_view = ClientView()
            result = client_view.create_client(session, token, client_data)
            
            if "error" in result:
                click.echo(f"Erreur: {result['error']}")
            else:
                click.echo(result["message"])
        
        @client.command("update")
        @click.argument("client_id", type=int)
        def update_client(client_id):
            """Met à jour un client existant"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour mettre à jour un client.")
                return
            
            # Récupérer le client actuel
            client_view = ClientView()
            current_client = client_view.get_client(session, token, client_id)
            
            if "error" in current_client:
                click.echo(f"Erreur: {current_client['error']}")
                return
                
            # Collecter les nouvelles données
            client_data = {}
            
            if click.confirm("Mettre à jour le nom?"):
                client_data["fullname"] = click.prompt("Nouveau nom complet")
                
            if click.confirm("Mettre à jour l'email?"):
                client_data["email"] = click.prompt("Nouvel email")
                
            if click.confirm("Mettre à jour le numéro de téléphone?"):
                client_data["phone_number"] = click.prompt("Nouveau numéro de téléphone", type=int)
                
            if click.confirm("Mettre à jour l'entreprise?"):
                client_data["enterprise"] = click.prompt("Nouvelle entreprise")
                
            if not client_data:
                click.echo("Aucune modification demandée.")
                return
                
            # Mettre à jour le client
            result = client_view.update_client(session, token, client_id, client_data)
            
            if "error" in result:
                click.echo(f"Erreur: {result['error']}")
            else:
                click.echo(result["message"])
        
        @client.command("delete")
        @click.argument("client_id", type=int)
        def delete_client(client_id):
            """Supprime un client existant"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour supprimer un client.")
                return
                
            if not click.confirm(f"Êtes-vous sûr de vouloir supprimer le client {client_id}?"):
                click.echo("Suppression annulée.")
                return
                
            client_view = ClientView()
            result = client_view.delete_client(session, token, client_id)
            
            if "error" in result:
                click.echo(f"Erreur: {result['error']}")
            else:
                click.echo(result["message"]) 