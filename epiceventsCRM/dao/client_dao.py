from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from epiceventsCRM.dao.base_dao import BaseDAO
from epiceventsCRM.models.models import Client


class ClientDAO(BaseDAO[Client]):
    """
    DAO pour les opérations sur les clients.
    """

    def __init__(self):
        """
        Initialise le DAO avec le modèle Client
        """
        super().__init__(Client)

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

    def get_by_sales_contact(self, db: Session, sales_contact_id: int) -> List[Client]:
        """
        Récupère tous les clients gérés par un commercial.

        Args:
            db (Session): La session de base de données
            sales_contact_id (int): L'ID du commercial

        Returns:
            List[Client]: Liste des clients gérés par le commercial
        """
        return list(db.scalars(select(Client).where(Client.sales_contact_id == sales_contact_id)))

    def create_client(self, db: Session, client_data: Dict) -> Client:
        """
        Crée un nouveau client avec dates automatiques.

        Args:
            db (Session): La session de base de données
            client_data (Dict): Les données du client

        Returns:
            Client: Le client créé
        """
        # Ajout des dates de création
        if "create_date" not in client_data:
            client_data["create_date"] = datetime.now()

        if "update_date" not in client_data:
            client_data["update_date"] = datetime.now()

        return self.create(db, client_data)

    def update_client(self, db: Session, client_id: int, client_data: Dict) -> Optional[Client]:
        """
        Met à jour un client.

        Args:
            db (Session): La session de base de données
            client_id (int): L'ID du client à mettre à jour
            client_data (Dict): Les nouvelles données

        Returns:
            Optional[Client]: Le client mis à jour ou None si non trouvé
        """
        client = self.get(db, client_id)
        if not client:
            return None

        # Mise à jour de la date de modification
        client_data["update_date"] = datetime.now()

        return self.update(db, client, client_data)

    def create(self, db: Session, client_data: Dict) -> Client:
        """Crée un nouveau client"""
        client = Client(
            fullname=client_data["fullname"],
            email=client_data["email"],
            phone_number=client_data["phone_number"],
            enterprise=client_data["enterprise"],
            sales_contact_id=client_data["sales_contact_id"],
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        return client

    def get(self, db: Session, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID"""
        return db.query(Client).filter(Client.id == client_id).first()
