from typing import List, Optional, Tuple, Dict

from sqlalchemy.orm import Session

from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Contract
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.sentry_utils import capture_exception, capture_message
from epiceventsCRM.utils.auth import verify_token


class ContractController(BaseController[Contract]):
    """
    Contrôleur pour la gestion des contrats.

    Gère les opérations CRUD sur les contrats avec des permissions spécifiques :
    - Les commerciaux peuvent voir les contrats de leurs clients
    - Le département gestion a un accès complet
    """

    def __init__(self):
        """Initialise le contrôleur des contrats avec le DAO approprié."""
        super().__init__(ContractDAO(), "contract")
        self.client_dao = ClientDAO()
        self.user_dao = UserDAO()

    @require_permission("read_contract")
    @capture_exception
    def get_all(
        self,
        token: str,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        unsigned_only: bool = False,
        unpaid_only: bool = False,
    ) -> Tuple[List[Contract], int]:
        """
        Récupère tous les contrats avec pagination et filtres optionnels.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            page: Numéro de la page (commence à 1)
            page_size: Nombre d'éléments par page
            unsigned_only (bool): Si True, filtre les contrats non signés (status=False).
            unpaid_only (bool): Si True, filtre les contrats non entièrement payés (remaining_amount > 0).

        Returns:
            Tuple[List[Contract], int]: (Liste des contrats filtrés, nombre total)
        """
        filters = {}
        if unsigned_only:
            filters["status"] = False
        if unpaid_only:
            # Utiliser une structure spéciale pour indiquer 'greater than 0'
            filters["remaining_amount"] = ("gt", 0)

        try:
            return self.dao.get_all(
                db, page=page, page_size=page_size, filters=filters if filters else None
            )
        except Exception as e:
            capture_exception(e)
            return [], 0

    @require_permission("create_contract")
    @capture_exception
    def create(self, token: str, db: Session, data: Dict) -> Optional[Contract]:
        """
        Crée un nouveau contrat.
        Seul le département Gestion a la permission (via le décorateur).
        Le commercial associé est déterminé à partir du client.

        Args:
            token: Token JWT (utilisé par le décorateur)
            db: Session de base de données
            data: Dictionnaire contenant les données du contrat.
                  Doit inclure 'client_id', 'amount'. 'status' est optionnel (défaut False).

        Returns:
            Le contrat créé si succès, None sinon.
        """
        client_id = data.get("client_id")
        amount = data.get("amount")
        status = data.get("status", False)  # Statut par défaut non signé

        if not client_id or amount is None:
            capture_message(
                "Données manquantes pour la création du contrat (client_id ou amount)",
                level="warning",
            )
            return None

        try:
            client = self.client_dao.get(db, client_id)
            if not client:
                capture_message(
                    f"Client avec ID {client_id} non trouvé lors de la création du contrat.",
                    level="warning",
                )
                return None

            if not client.sales_contact_id:
                capture_message(
                    f"Le client {client_id} n'a pas de commercial assigné.", level="warning"
                )
                return None

            created_contract = self.dao.create_contract(
                db=db,
                client_id=client_id,
                amount=amount,
                sales_contact_id=client.sales_contact_id,
                status=status,
            )

            if created_contract:
                capture_message(
                    f"Contrat {created_contract.id} créé pour le client {client_id}", level="info"
                )
            return created_contract

        except Exception as e:
            capture_exception(e)
            return None

    @require_permission("read_contract")
    def get_contracts_by_client(self, token: str, db: Session, client_id: int) -> List[Contract]:
        """
        Récupère tous les contrats d'un client.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            client_id: ID du client

        Returns:
            Liste des contrats du client

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        return self.dao.get_by_client(db, client_id)

    @require_permission("read_contract")
    def get_contracts_by_commercial(self, token: str, db: Session) -> List[Contract]:
        """
        Récupère tous les contrats des clients d'un commercial.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données

        Returns:
            Liste des contrats des clients du commercial connecté

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de lecture
        """
        payload = verify_token(token)
        if not payload or "sub" not in payload:
            return []

        user_id = payload["sub"]
        return self.dao.get_by_commercial(db, user_id)

    @require_permission("update_contract")
    @capture_exception
    def update_contract(
        self, token: str, db: Session, contract_id: int, update_data: Dict
    ) -> Optional[Contract]:
        """
        Met à jour un contrat avec les données fournies.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            contract_id: ID du contrat
            update_data: Données à mettre à jour (status, amount, etc.)

        Returns:
            Le contrat mis à jour si l'opération réussit, None sinon

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de mise à jour
        """
        try:
            contract = self.dao.get(db, contract_id)
            if not contract:
                capture_message(
                    f"Tentative de mise à jour d'un contrat inexistant: {contract_id}",
                    level="warning",
                )
                return None

            payload = verify_token(token)
            if not payload or "sub" not in payload:
                capture_message("Tentative de mise à jour avec un token invalide", level="warning")
                return None

            user_id = payload["sub"]
            department = payload.get("department", "").lower()

            # Journaliser la tentative de mise à jour
            capture_message(
                f"Tentative de mise à jour du contrat {contract_id} par l'utilisateur {user_id} (département: {department})",
                level="info",
            )

            if department == "commercial":
                if contract.client.sales_contact_id != user_id:
                    capture_message(
                        f"Accès refusé: le commercial {user_id} n'est pas associé au client du contrat {contract_id}",
                        level="warning",
                    )
                    return None
            elif department != "gestion":
                capture_message(
                    f"Accès refusé: le département {department} n'a pas les permissions nécessaires",
                    level="warning",
                )
                return None

            old_status = contract.status

            updated_contract = self.dao.update(db, contract, update_data)

            # Journaliser la signature si le statut a changé de False à True
            if (
                updated_contract
                and "status" in update_data
                and update_data["status"] is True
                and not old_status
            ):
                capture_message(
                    f"Contrat {contract_id} signé par l'utilisateur {user_id}",
                    level="info",
                    extra={
                        "contract_id": contract_id,
                        "user_id": user_id,
                        "department": department,
                        "client_id": contract.client_id,
                        "amount": contract.amount,
                        "old_status": old_status,
                        "new_status": update_data["status"],
                    },
                )

            return updated_contract

        except Exception as e:
            capture_exception(e)
            return None

    @require_permission("delete_contract")
    @capture_exception
    def delete(self, token: str, db: Session, contract_id: int) -> bool:
        """
        Supprime un contrat.
        Seul le département Gestion a la permission (via le décorateur).

        Args:
            token: Token JWT (utilisé par le décorateur)
            db: Session de base de données
            contract_id: ID du contrat à supprimer

        Returns:
            True si la suppression a réussi, False sinon.
        """

        contract = self.dao.get(db, contract_id)
        if not contract:
            capture_message(
                f"Tentative de suppression d'un contrat inexistant: {contract_id}", level="warning"
            )
            return False

        try:
            deleted = self.dao.delete(db, contract_id)
            if deleted:
                capture_message(f"Contrat {contract_id} supprimé avec succès.", level="info")
            else:
                capture_message(
                    f"Échec de la suppression du contrat {contract_id} (DAO a retourné False).",
                    level="warning",
                )
            return deleted
        except Exception as e:
            capture_exception(e)
            return False
