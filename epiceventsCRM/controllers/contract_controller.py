from datetime import datetime
from typing import List, Optional, Tuple, Union, Dict

import jwt
from sqlalchemy.orm import Session

from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Client, Contract, User
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.sentry_utils import capture_exception, capture_message
from epiceventsCRM.utils.token_manager import decode_token


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

        # Alias pour la compatibilité avec les tests
        self.list_contracts = self.get_all
        self.get_contract = self.get
        # Ne pas écraser update_contract car elle a des décorateurs spécifiques

    @require_permission("create_contract")
    def create(self, token: str, db: Session, contract_data: Dict) -> Optional[Contract]:
        """
        Crée un nouveau contrat.

        Args:
            token: Token JWT de l'utilisateur
            db: Session de base de données
            contract_data: Données du contrat à créer

        Returns:
            Le contrat créé si l'opération réussit, None sinon

        Raises:
            ValueError: Si des champs obligatoires sont manquants
            PermissionError: Si l'utilisateur n'a pas la permission de création
        """
        try:
            # Vérification des champs obligatoires
            required_fields = ["client_id", "amount", "remaining_amount", "status"]
            for field in required_fields:
                if field not in contract_data:
                    print(f"Erreur: champ obligatoire manquant: {field}")
                    return None

            # Vérification que le client existe
            client = self.client_dao.get(db, contract_data["client_id"])
            if not client:
                print(f"Erreur: client avec ID {contract_data['client_id']} non trouvé")
                return None

            # Création du contrat
            contract = self.dao.create(
                db,
                client_id=contract_data["client_id"],
                amount=contract_data["amount"],
                remaining_amount=contract_data["remaining_amount"],
                status=contract_data["status"],
            )

            if not contract:
                print("Erreur: création du contrat échouée")
                return None

            return contract
        except Exception as e:
            print(f"Erreur lors de la création du contrat: {str(e)}")
            return None

    @capture_exception
    def create_contract(
        self, token: str, db: Session, client_id: int, amount: float, status: bool = False
    ) -> Tuple[bool, Union[Contract, str]]:
        """
        Crée un nouveau contrat.

        Args:
            token: Token JWT de l'utilisateur connecté
            db: Session de base de données
            client_id: ID du client associé au contrat
            amount: Montant total du contrat
            status: Statut du contrat (False = non signé, True = signé)

        Returns:
            Tuple[bool, Union[Contract, str]]: (succès, contrat ou message d'erreur)
        """
        try:
            # Vérifier l'authentification et les autorisations
            payload = decode_token(token)
            if not payload:
                return False, "Token invalide"

            # Récupérer l'ID de l'utilisateur depuis le token
            user_id = payload.get("sub")
            if not user_id:
                return False, "Token invalide: ID utilisateur manquant"

            # Obtenez l'utilisateur à partir de l'ID
            user = self.user_dao.get(db, user_id)
            if not user:
                return False, f"Utilisateur avec ID {user_id} non trouvé"

            # Vérifier si l'utilisateur est dans le département gestion
            department_name = user.department.departement_name.lower()
            if department_name != "gestion":
                return False, "Accès refusé: seul le département gestion peut créer des contrats"

            # Vérifier si le client existe et récupérer son commercial
            client = self.client_dao.get(db, client_id)
            if not client:
                return False, f"Client avec ID {client_id} non trouvé"

            if not client.sales_contact_id:
                return False, f"Le client {client_id} n'a pas de commercial assigné"

            # Créer le contrat avec le commercial du client
            contract = self.dao.create_contract(
                db=db, 
                client_id=client_id, 
                amount=amount, 
                sales_contact_id=client.sales_contact_id, 
                status=status
            )

            return True, contract

        except Exception as e:
            capture_exception(e)
            return False, f"Erreur lors de la création du contrat: {str(e)}"

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
        # Récupérer l'ID de l'utilisateur depuis le token
        payload = decode_token(token)
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
            # Récupérer le contrat existant
            contract = self.dao.get(db, contract_id)
            if not contract:
                capture_message(
                    f"Tentative de mise à jour d'un contrat inexistant: {contract_id}",
                    level="warning"
                )
                return None

            # Vérifier les permissions
            payload = decode_token(token)
            if not payload or "sub" not in payload:
                capture_message(
                    "Tentative de mise à jour avec un token invalide",
                    level="warning"
                )
                return None

            user_id = payload["sub"]
            department = payload.get("department", "").lower()

            # Journaliser la tentative de mise à jour
            capture_message(
                f"Tentative de mise à jour du contrat {contract_id} par l'utilisateur {user_id} (département: {department})",
                level="info"
            )

            # Vérifier les permissions selon le département
            if department == "commercial":
                if contract.client.sales_contact_id != user_id:
                    capture_message(
                        f"Accès refusé: le commercial {user_id} n'est pas associé au client du contrat {contract_id}",
                        level="warning"
                    )
                    return None
            elif department != "gestion":
                capture_message(
                    f"Accès refusé: le département {department} n'a pas les permissions nécessaires",
                    level="warning"
                )
                return None

            # Sauvegarder l'ancien statut avant la mise à jour
            old_status = contract.status

            # Mettre à jour le contrat en utilisant l'objet contract au lieu de contract_id
            updated_contract = self.dao.update(db, contract, update_data)

            # Journaliser la signature si le statut a changé de False à True
            if (
                updated_contract 
                and "status" in update_data 
                and update_data["status"] is True 
                and old_status == False
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
                        "new_status": update_data["status"]
                    }
                )

            return updated_contract

        except Exception as e:
            capture_exception(e)
            return None

    def delete_contract(self, token: str, contract_id: int) -> Tuple[bool, str]:
        """
        Supprime un contrat.

        Args:
            token: Token JWT de l'utilisateur connecté
            contract_id: ID du contrat à supprimer

        Returns:
            Tuple[bool, str]: (succès, message de confirmation ou d'erreur)

        Raises:
            PermissionError: Si l'utilisateur n'a pas la permission de suppression
        """
        try:
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
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
