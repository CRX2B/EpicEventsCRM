from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.models.models import Client
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.auth import verify_token
from epiceventsCRM.utils.sentry_utils import capture_exception, capture_message
from epiceventsCRM.utils.validators import is_valid_email_format, is_valid_phone_format


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
        payload = verify_token(token)
        if not payload or "sub" not in payload:
            return []

        user_id = payload["sub"]
        return self.dao.get_by_sales_contact(db, user_id)

    @require_permission("update_client")
    def update_client_commercial(
        self, token: str, db: Session, client_id: int, commercial_id: int
    ) -> Optional[Client]:
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

        payload = verify_token(token)
        if not payload or "sub" not in payload or "department" not in payload:
            return None

        user_id = payload["sub"]
        department = payload["department"]

        if department == "commercial" and client.sales_contact_id != user_id:
            capture_message(
                f"Tentative non autorisée de MAJ commercial {commercial_id} pour client {client_id} par user {user_id}",
                level="warning",
            )
            return None

        return self.dao.update_commercial(db, client, commercial_id)

    @require_permission("create_client")
    def create(self, token: str, db: Session, client_data: Dict) -> Optional[Client]:
        """
        Crée un nouveau client en assignant automatiquement le commercial.
        Avec validation des formats pour email et phone_number.

        Args:
            token (str): Le token JWT
            db (Session): La session de base de données
            client_data (Dict): Les données du client

        Returns:
            Optional[Client]: Le client créé
        """
        try:
            payload = verify_token(token)

            if not payload or "sub" not in payload:
                capture_message(
                    "Tentative de création de client avec token invalide", level="error"
                )
                return None

            client_data["sales_contact_id"] = payload["sub"]

            # --- Validation ---
            errors = []
            required_fields = ["fullname", "email", "phone_number", "enterprise"]
            for field in required_fields:
                if field not in client_data or not client_data[field]:
                    errors.append(f"Champ obligatoire manquant ou vide: {field}")

            email = client_data.get("email")
            phone = client_data.get("phone_number")

            if email and not is_valid_email_format(email):
                errors.append("Format d'email invalide.")

            if phone and not is_valid_phone_format(phone):
                errors.append("Format de numéro de téléphone invalide.")

            if client_data.get("fullname") and len(client_data["fullname"]) > 100:
                errors.append("Nom complet trop long (max 100 caractères).")
            if client_data.get("enterprise") and len(client_data["enterprise"]) > 100:
                errors.append("Nom d'entreprise trop long (max 100 caractères).")

            if errors:
                error_message = "Erreurs de validation lors de la création du client: " + ", ".join(
                    errors
                )
                capture_message(error_message, level="warning")
                return None
            # --- Fin Validation ---

            client = self.dao.create_client(db, client_data)
            if not client:
                capture_message(
                    "Erreur: création du client échouée après validation", level="error"
                )
                return None

            return client
        except Exception as e:
            capture_exception(e)
            return None

    @require_permission("read_client")
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
        return self.dao.get(db, client_id)

    @require_permission("read_client")
    def get_all_clients(
        self, db: Session, token: str, skip: int = 0, limit: int = 100
    ) -> List[Client]:
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
        return self.dao.get_all(db, skip=skip, limit=limit)

    @require_permission("read_client")
    def get_my_clients(self, db: Session, token: str) -> List[Client]:
        """
        Récupère tous les clients gérés par l'utilisateur connecté.

        Args:
            db (Session): La session de base de données
            token (str): Le token JWT

        Returns:
            List[Client]: Liste des clients gérés par l'utilisateur
        """
        user_info = verify_token(token)
        if not user_info or "sub" not in user_info:
            capture_message(
                "Token invalide ou 'sub' manquant dans get_my_clients après vérification permission",
                level="warning",
            )
            return []

        return self.dao.get_by_sales_contact(db, user_info["sub"])

    @require_permission("update_client")
    def update_client(
        self, db: Session, token: str, client_id: int, client_data: Dict
    ) -> Optional[Client]:
        """
        Met à jour un client.
        Avec validation des formats pour email et phone_number.

        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            client_id (int): L'ID du client
            client_data (Dict): Les nouvelles données

        Returns:
            Optional[Client]: Le client mis à jour si la permission est accordée, None sinon
        """
        client = self.dao.get(db, client_id)
        if not client:
            return None

        # Vérification métier spécifique : le commercial ne modifie que ses clients
        user_info = verify_token(token)
        if (
            not user_info
            or "sub" not in user_info
            or (
                client.sales_contact_id != user_info["sub"]
                and user_info.get("department") != "gestion"
            )
        ):
            capture_message(
                f"Tentative non autorisée de MAJ client {client_id} par user {user_info.get('sub')}",
                level="warning",
            )
            return None

        # --- Validation ---
        errors = []
        if "email" in client_data:
            email = client_data["email"]
            if not email or not is_valid_email_format(email):
                errors.append("Format d'email invalide.")

        if "phone_number" in client_data:
            phone = client_data["phone_number"]
            if not phone or not is_valid_phone_format(phone):
                errors.append("Format de numéro de téléphone invalide.")

        if "fullname" in client_data and len(client_data["fullname"]) > 100:
            errors.append("Nom complet trop long (max 100 caractères).")
        if "enterprise" in client_data and len(client_data["enterprise"]) > 100:
            errors.append("Nom d'entreprise trop long (max 100 caractères).")

        if errors:
            error_message = "Erreurs de validation lors de la mise à jour du client: " + ", ".join(
                errors
            )
            capture_message(error_message, level="warning")
            return None
        # --- Fin Validation ---

        updated_client = self.dao.update_client(db, client_id, client_data)
        return updated_client

    @require_permission("delete_client")
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
        client = self.dao.get(db, client_id)
        if not client:
            return False

        # Vérification métier spécifique : le commercial ne supprime que ses clients
        user_info = verify_token(token)
        if (
            not user_info
            or "sub" not in user_info
            or (
                client.sales_contact_id != user_info["sub"]
                and user_info.get("department") != "gestion"
            )
        ):
            capture_message(
                f"Tentative non autorisée de suppression client {client_id} par user {user_info.get('sub')}",
                level="warning",
            )
            return False

        return self.dao.delete(db, client_id)
