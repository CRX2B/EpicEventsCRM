from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from epiceventsCRM.models.models import Client

class ClientDAO:
    """
    DAO pour les opérations sur les clients.
    """
    
    def __init__(self, session: Session = None):
        """
        Initialise le DAO avec une session optionnelle
        
        Args:
            session (Session, optional): La session de base de données
        """
        self.session = session
    
    def create(self, db: Session, client_data: Dict) -> Client:
        """
        Crée un nouveau client.
        
        Args:
            db (Session): La session de base de données
            client_data (Dict): Les données du client
            
        Returns:
            Client: Le client créé
        """
        # Ajout des dates de création et mise à jour
        client_data["create_date"] = datetime.now()
        client_data["update_date"] = datetime.now()
        
        client = Client(**client_data)
        db.add(client)
        db.commit()
        db.refresh(client)
        return client
    
    def get(self, db: Session, client_id: int) -> Optional[Client]:
        """
        Récupère un client par son ID.
        
        Args:
            db (Session): La session de base de données
            client_id (int): L'ID du client
            
        Returns:
            Optional[Client]: Le client si trouvé, None sinon
        """
        return db.query(Client).filter(Client.id == client_id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[Client]:
        """
        Récupère un client par son email.
        
        Args:
            db (Session): La session de base de données
            email (str): L'email du client
            
        Returns:
            Optional[Client]: Le client si trouvé, None sinon
        """
        return db.query(Client).filter(Client.email == email).first()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Client]:
        """
        Récupère tous les clients avec pagination.
        
        Args:
            db (Session): La session de base de données
            skip (int): Nombre de clients à sauter
            limit (int): Nombre maximum de clients à retourner
            
        Returns:
            List[Client]: Liste des clients
        """
        return db.query(Client).offset(skip).limit(limit).all()
    
    def get_by_sales_contact(self, db: Session, sales_contact_id: int) -> List[Client]:
        """
        Récupère tous les clients gérés par un commercial.
        
        Args:
            db (Session): La session de base de données
            sales_contact_id (int): L'ID du commercial
            
        Returns:
            List[Client]: Liste des clients gérés par le commercial
        """
        return db.query(Client).filter(Client.sales_contact_id == sales_contact_id).all()
    
    def update(self, db: Session, client: Client, client_data: Dict) -> Client:
        """
        Met à jour un client.
        
        Args:
            db (Session): La session de base de données
            client (Client): Le client à mettre à jour
            client_data (Dict): Les nouvelles données
            
        Returns:
            Client: Le client mis à jour
        """
        # Mise à jour de la date de modification
        client_data["update_date"] = datetime.now()
        
        for key, value in client_data.items():
            setattr(client, key, value)
            
        db.commit()
        db.refresh(client)
        return client
    
    def delete(self, db: Session, client_id: int) -> bool:
        """
        Supprime un client.
        
        Args:
            db (Session): La session de base de données
            client_id (int): L'ID du client
            
        Returns:
            bool: True si le client a été supprimé, False sinon
        """
        client = self.get(db, client_id)
        if not client:
            return False
            
        db.delete(client)
        db.commit()
        return True
        
    # Ajout de méthodes pour compatibilité avec le controller
    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """
        Récupère un client par son ID en utilisant la session stockée
        
        Args:
            client_id (int): L'ID du client
            
        Returns:
            Optional[Client]: Le client si trouvé, None sinon
        """
        if not self.session:
            raise ValueError("Session not provided")
        return self.get(self.session, client_id) 