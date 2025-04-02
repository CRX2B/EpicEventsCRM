from typing import List, Dict, Optional, Tuple, Any, Union
from sqlalchemy.orm import Session
import jwt
from datetime import datetime

from epiceventsCRM.dao.event_dao import EventDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Event, User, Department


class EventController:
    """
    Contrôleur pour gérer les événements
    """
    
    def __init__(self, session: Session):
        """
        Initialise le contrôleur avec une session DB
        
        Args:
            session: Session SQLAlchemy active
        """
        self.session = session
        self.event_dao = EventDAO(session)
        self.contract_dao = ContractDAO(session)
        self.client_dao = ClientDAO(session)
        self.user_dao = UserDAO(session)

    def get_event(self, token: str, event_id: int) -> Tuple[bool, Union[Event, str]]:
        """
        Récupère un événement par son ID
        
        Args:
            token: Token JWT de l'utilisateur connecté
            event_id: ID de l'événement à récupérer
            
        Returns:
            Tuple[bool, Union[Event, str]]: (succès, événement ou message d'erreur)
        """
        try:
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Récupérer l'événement
            event = self.event_dao.get_event_by_id(event_id)
            if not event:
                return False, f"Événement avec ID {event_id} non trouvé"
            
            # Tous les collaborateurs peuvent lire tous les événements
            return True, event
                
        except Exception as e:
            return False, f"Erreur lors de la récupération de l'événement: {str(e)}"

    def list_events(self, token: str, filter_by_support: bool = False) -> Tuple[bool, Union[List[Event], str]]:
        """
        Liste les événements accessibles par l'utilisateur
        
        Args:
            token: Token JWT de l'utilisateur connecté
            filter_by_support: Si True et l'utilisateur est du support, renvoie uniquement les événements assignés
            
        Returns:
            Tuple[bool, Union[List[Event], str]]: (succès, liste d'événements ou message d'erreur)
        """
        try:
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
            
            department_name = user.department.departement_name.lower()
            
            # Si l'utilisateur est du support et souhaite filtrer ses événements
            if department_name == "support" and filter_by_support:
                events = self.event_dao.get_events_by_support_contact(user_id)
                return True, events
            
            # Par défaut, tous les collaborateurs voient tous les événements
            events = self.event_dao.get_all_events()
            return True, events
                
        except Exception as e:
            return False, f"Erreur lors de la récupération des événements: {str(e)}"

    def create_event(self, token: str, event_data: Dict) -> Tuple[bool, Union[Event, str]]:
        """
        Crée un nouvel événement
        
        Args:
            token: Token JWT de l'utilisateur connecté
            event_data: Données de l'événement
            
        Returns:
            Tuple[bool, Union[Event, str]]: (succès, événement créé ou message d'erreur)
        """
        try:
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
            
            # Vérifier si l'utilisateur a le droit de créer un événement
            department_name = user.department.departement_name.lower()
            if department_name not in ["gestion", "commercial"]:
                return False, "Accès refusé: seuls les commerciaux et la gestion peuvent créer des événements"
            
            # Vérifier si le contrat existe
            contract_id = event_data.get("contract_id")
            contract = self.contract_dao.get_contract_by_id(contract_id)
            if not contract:
                return False, f"Contrat avec ID {contract_id} non trouvé"
            
            # Pour les commerciaux, vérifier si le contrat leur appartient
            if department_name == "commercial" and contract.sales_contact_id != user_id:
                return False, "Accès refusé: ce contrat n'est pas géré par vous"
                
            # Créer l'événement
            event = self.event_dao.create_event(
                name=event_data.get("name"),
                contract_id=contract_id,
                client_id=contract.client_id,
                start_event=event_data.get("start_event"),
                end_event=event_data.get("end_event"),
                location=event_data.get("location"),
                support_contact_id=event_data.get("support_contact_id"),
                attendees=event_data.get("attendees"),
                notes=event_data.get("notes")
            )
            
            return True, event
            
        except Exception as e:
            return False, f"Erreur lors de la création de l'événement: {str(e)}"

    def update_event(self, token: str, event_id: int, event_data: Dict) -> Tuple[bool, Union[Event, str]]:
        """
        Met à jour un événement existant
        
        Args:
            token: Token JWT de l'utilisateur connecté
            event_id: ID de l'événement à mettre à jour
            event_data: Nouvelles données de l'événement
            
        Returns:
            Tuple[bool, Union[Event, str]]: (succès, événement mis à jour ou message d'erreur)
        """
        try:
            # Vérifier si l'événement existe et si l'utilisateur y a accès
            success, result = self.get_event(token, event_id)
            if not success:
                return False, result
                
            event = result
            
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Vérifier les permissions selon le département
            department_name = user.department.departement_name.lower()
            
            # Déterminer quels champs peuvent être modifiés selon le département
            allowed_fields = []
            
            if department_name == "gestion":
                # La gestion peut tout modifier
                allowed_fields = ["name", "contract_id", "client_id", "start_event", "end_event", 
                                  "location", "support_contact_id", "attendees", "notes"]
            elif department_name == "commercial":
                # Les commerciaux ne peuvent pas modifier les événements selon le cahier des charges
                return False, "Accès refusé: les commerciaux ne peuvent pas modifier les événements"
            elif department_name == "support":
                # Le support ne peut modifier que les notes de l'événement assigné
                if event.support_contact_id != user_id:
                    return False, "Accès refusé: cet événement ne vous est pas assigné"
                allowed_fields = ["notes"]
            else:
                return False, "Accès refusé: département non reconnu"
            
            # Filtrer les champs autorisés
            filtered_data = {k: v for k, v in event_data.items() if k in allowed_fields}
            
            if not filtered_data:
                return False, "Aucun champ modifiable fourni"
                
            # Mettre à jour l'événement
            updated_event = self.event_dao.update_event(event_id, filtered_data)
            return True, updated_event
            
        except Exception as e:
            return False, f"Erreur lors de la mise à jour de l'événement: {str(e)}"

    def delete_event(self, token: str, event_id: int) -> Tuple[bool, str]:
        """
        Supprime un événement
        
        Args:
            token: Token JWT de l'utilisateur connecté
            event_id: ID de l'événement à supprimer
            
        Returns:
            Tuple[bool, str]: (succès, message de résultat)
        """
        try:
            # Vérifier si l'événement existe et si l'utilisateur y a accès
            success, result = self.get_event(token, event_id)
            if not success:
                return False, result
                
            event = result
            
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Vérifier les permissions selon le département
            department_name = user.department.departement_name.lower()
            
            # Seul le département gestion peut supprimer un événement
            if department_name == "gestion":
                # La gestion peut supprimer n'importe quel événement
                pass
            else:
                return False, "Accès refusé: seul le département gestion peut supprimer des événements"
                
            # Supprimer l'événement
            success = self.event_dao.delete_event(event_id)
            if success:
                return True, "Événement supprimé avec succès"
            else:
                return False, "Échec de la suppression de l'événement"
                
        except Exception as e:
            return False, f"Erreur lors de la suppression de l'événement: {str(e)}"

    def assign_support_contact(self, token: str, event_id: int, support_contact_id: int) -> Tuple[bool, Union[Event, str]]:
        """
        Assigne un contact support à un événement
        
        Args:
            token: Token JWT de l'utilisateur connecté
            event_id: ID de l'événement
            support_contact_id: ID du contact support
            
        Returns:
            Tuple[bool, Union[Event, str]]: (succès, événement mis à jour ou message d'erreur)
        """
        try:
            # Vérifier si l'événement existe et si l'utilisateur y a accès
            success, result = self.get_event(token, event_id)
            if not success:
                return False, result
                
            event = result
            
            # Vérifier l'authentification
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = self.user_dao.get_user_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
                
            # Vérifier les permissions selon le département
            department_name = user.department.departement_name.lower()
            
            # Seule la gestion peut assigner un contact support
            if department_name == "gestion":
                # La gestion peut assigner n'importe quel événement
                pass
            else:
                return False, "Accès refusé: seul le département gestion peut assigner des contacts support"
                
            # Vérifier si le contact support existe et est bien du département support
            support_user = self.user_dao.get_user_by_id(support_contact_id)
            if not support_user:
                return False, f"Utilisateur avec ID {support_contact_id} non trouvé"
                
            if support_user.department.departement_name.lower() != "support":
                return False, "L'utilisateur assigné doit être du département support"
                
            # Assigner le contact support
            updated_event = self.event_dao.assign_support_contact(event_id, support_contact_id)
            if updated_event:
                return True, updated_event
            else:
                return False, "Échec de l'assignation du contact support"
                
        except Exception as e:
            return False, f"Erreur lors de l'assignation du contact support: {str(e)}" 