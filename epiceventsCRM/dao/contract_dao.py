from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from epiceventsCRM.dao.base_dao import BaseDAO
from epiceventsCRM.models.models import Contract


class ContractDAO(BaseDAO[Contract]):
    """
    Data Access Object pour les contrats
    """

    def __init__(self):
        """
        Initialise la classe ContractDAO avec le modèle Contract
        """
        super().__init__(Contract)

    def get(self, db: Session, contract_id: int) -> Optional[Contract]:
        """
        Récupère une entité Contrat par son ID.

        Args:
            db (Session): La session de base de données
            contract_id (int): L'ID de l'entité Contrat

        Returns:
            Optional[Contract]: L'entité Contrat si trouvée, None sinon
        """
        return db.query(Contract).filter(Contract.id == contract_id).first()

    def create_contract(
        self,
        db: Session,
        client_id: int,
        amount: float,
        sales_contact_id: int,
        status: bool = False,
    ) -> Contract:
        """
        Crée un nouveau contrat

        Args:
            db (Session): Session SQLAlchemy active
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
            sales_contact_id=sales_contact_id,
        )
        db.add(contract)
        db.commit()
        return contract

    def get_by_client(self, db: Session, client_id: int) -> List[Contract]:
        """
        Récupère tous les contrats associés à un client

        Args:
            db (Session): Session SQLAlchemy active
            client_id: ID du client

        Returns:
            List[Contract]: Liste des contrats du client
        """
        return list(db.scalars(select(Contract).where(Contract.client_id == client_id)))

    def get_by_sales_contact(self, db: Session, sales_contact_id: int) -> List[Contract]:
        """
        Récupère tous les contrats associés à un commercial

        Args:
            db (Session): Session SQLAlchemy active
            sales_contact_id: ID du commercial

        Returns:
            List[Contract]: Liste des contrats gérés par le commercial
        """
        return list(
            db.scalars(select(Contract).where(Contract.sales_contact_id == sales_contact_id))
        )
