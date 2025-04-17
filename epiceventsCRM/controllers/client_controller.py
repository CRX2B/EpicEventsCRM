from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from epiceventsCRM.controllers.base_controller import BaseController
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.models.models import Client
from epiceventsCRM.utils.permissions import require_permission
from epiceventsCRM.utils.auth import verify_token
from epiceventsCRM.utils.sentry_utils import capture_exception, capture_message


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

        # Mise à jour du commercial
        return self.dao.update_commercial(db, client, commercial_id)

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
        try:
            # Récupération des informations de l'utilisateur depuis le token
            payload = verify_token(token)

            if not payload or "sub" not in payload:
                capture_message(
                    "Tentative de création de client avec token invalide", level="error"
                )
                return None

            # Attribution du commercial (l'utilisateur connecté) au client
            client_data["sales_contact_id"] = payload["sub"]

            # Vérification des champs obligatoires
            required_fields = ["fullname", "email", "phone_number", "enterprise"]
            for field in required_fields:
                if field not in client_data:
                    capture_message(f"Erreur: champ obligatoire manquant: {field}", level="error")
                    return None

            # Appeler la méthode create_client du DAO qui définit les dates automatiquement
            client = self.dao.create_client(db, client_data)
            if not client:
                capture_message("Erreur: création du client échouée", level="error")
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
        # Récupération des informations de l'utilisateur depuis le token
        user_info = verify_token(token)
        if not user_info or "sub" not in user_info:
            capture_message(
                "Token invalide ou 'sub' manquant dans get_my_clients après vérification permission",
                level="warning",
            )
            return []

        # Récupération des clients gérés par l'utilisateur
        return self.dao.get_by_sales_contact(db, user_info["sub"])

    @require_permission("update_client")
    def update_client(
        self, db: Session, token: str, client_id: int, client_data: Dict
    ) -> Optional[Client]:
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
        # Vérification que le client existe
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

        return self.dao.update_client(db, client_id, client_data)

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
        # Vérification que le client existe
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
