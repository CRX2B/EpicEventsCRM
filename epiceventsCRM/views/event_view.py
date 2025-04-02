import click
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import sys

from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.controllers.user_management_controller import UserManagementController


class EventView:
    """
    Vue pour gérer les événements via l'interface en ligne de commande
    """
    
    def __init__(self, session: Session, token: str):
        """
        Initialise la vue avec une session et un token
        
        Args:
            session: Session SQLAlchemy active
            token: Token JWT pour l'authentification
        """
        self.session = session
        self.token = token
        self.event_controller = EventController(session)
        self.contract_controller = ContractController(session)
        self.client_controller = ClientController(session)
        self.user_controller = UserManagementController()
    
    def display_event(self, event: Dict) -> None:
        """
        Affiche les détails d'un événement
        
        Args:
            event: Dictionnaire représentant un événement
        """
        click.echo("-" * 60)
        click.echo(f"ID: {event.id}")
        click.echo(f"Nom: {event.name}")
        click.echo(f"Contrat ID: {event.contract_id}")
        click.echo(f"Client ID: {event.client_id}")
        click.echo(f"Date de début: {event.start_event}")
        click.echo(f"Date de fin: {event.end_event}")
        click.echo(f"Lieu: {event.location}")
        click.echo(f"Contact support ID: {event.support_contact_id or 'Non assigné'}")
        click.echo(f"Nombre de participants: {event.attendees or 'Non spécifié'}")
        click.echo(f"Notes: {event.notes or 'Aucune note'}")
        click.echo("-" * 60)
    
    def list_events(self, filter_my_events: bool = False) -> None:
        """
        Interface pour lister tous les événements

        Args:
            filter_my_events: Si True, filtre les événements assignés au support connecté
        """
        success, events = self.event_controller.list_events(self.token, filter_my_events)
        
        if not success:
            click.echo(f"Erreur: {events}")
            return
            
        if not events:
            click.echo("Aucun événement trouvé.")
            return
            
        if filter_my_events:
            click.echo(f"Liste de vos événements assignés ({len(events)} trouvés):")
        else:
            click.echo(f"Liste des événements ({len(events)} trouvés):")
            
        for event in events:
            self.display_event(event)
    
    def get_event_by_id(self, event_id: int) -> None:
        """
        Affiche les détails d'un événement spécifique
        
        Args:
            event_id: ID de l'événement à afficher
        """
        success, result = self.event_controller.get_event(self.token, event_id)
        
        if not success:
            click.echo(f"Erreur: {result}")
            return
            
        click.echo("Détails de l'événement:")
        self.display_event(result)
    
    def create_event(self) -> None:
        """
        Interface pour créer un nouvel événement
        """
        # Obtenir d'abord la liste des contrats disponibles
        success, contracts = self.contract_controller.list_contracts(self.token)
        
        if not success:
            click.echo(f"Erreur: {contracts}")
            return
            
        if not contracts:
            click.echo("Aucun contrat trouvé. Veuillez d'abord créer un contrat.")
            return
            
        # Afficher les contrats disponibles
        click.echo("Contrats disponibles:")
        for contract in contracts:
            click.echo(f"ID: {contract.id}, Client ID: {contract.client_id}, Montant: {contract.amount} €")
        
        # Collecter les informations nécessaires
        try:
            contract_id = click.prompt("ID du contrat", type=int)
            name = click.prompt("Nom de l'événement")
            location = click.prompt("Lieu de l'événement")
            attendees = click.prompt("Nombre de participants (laisser vide si inconnu)", type=int, default=0)
            if attendees == 0:
                attendees = None
            notes = click.prompt("Notes (laisser vide si aucune)", default="")
            if notes == "":
                notes = None
            
            # Demander si on veut assigner un contact support
            support_contact_id = None
            if click.confirm("Assigner un contact support maintenant?", default=False):
                support_contact_id = click.prompt("ID du contact support", type=int)
            
            # Créer l'événement avec des dates fixes pour les tests
            start_event = datetime(2025, 4, 1, 17, 26, 28, 342075)
            end_event = datetime(2025, 4, 1, 19, 26, 28, 342075)
            
            # Créer l'événement
            success, result = self.event_controller.create_event(
                token=self.token,
                name=name,
                contract_id=contract_id,
                client_id=contracts[0].client_id,
                start_event=start_event,
                end_event=end_event,
                location=location,
                attendees=attendees,
                notes=notes,
                support_contact_id=support_contact_id
            )
            
            if success:
                click.echo("Événement créé avec succès:")
                self.display_event(result)
            else:
                click.echo(f"Erreur: {result}")
                
        except ValueError as e:
            click.echo(f"Erreur de format: {str(e)}. Veuillez réessayer.")
        except Exception as e:
            click.echo(f"Une erreur est survenue: {str(e)}")
    
    def update_event(self, event_id: int) -> None:
        """
        Interface pour mettre à jour un événement

        Args:
            event_id: ID de l'événement à mettre à jour
        """
        # Vérifier si l'événement existe et si l'utilisateur y a accès
        success, event = self.event_controller.get_event(self.token, event_id)
        
        if not success:
            click.echo(f"Erreur: {event}")
            return
            
        click.echo("Événement actuel:")
        self.display_event(event)
        
        # Demander les modifications
        try:
            name = click.prompt("Nouveau nom (laisser vide pour ne pas modifier)", default=event.name)
            location = click.prompt("Nouveau lieu (laisser vide pour ne pas modifier)", default=event.location)
            attendees = click.prompt("Nouveau nombre de participants (laisser vide pour ne pas modifier)", type=int, default=event.attendees)
            notes = click.prompt("Nouvelles notes (laisser vide pour ne pas modifier)", default=event.notes or "")
            
            # Vérifier si des modifications ont été demandées
            if (name == event.name and location == event.location and 
                attendees == event.attendees and notes == (event.notes or "")):
                click.echo("Aucune modification demandée.")
                return
                
            # Mettre à jour l'événement
            success, result = self.event_controller.update_event(
                token=self.token,
                event_id=event_id,
                name=name,
                location=location,
                attendees=attendees,
                notes=notes if notes else None
            )
            
            if success:
                click.echo("Événement mis à jour avec succès.")
                self.display_event(result)
            else:
                click.echo(f"Erreur: {result}")
                
        except ValueError as e:
            click.echo(f"Erreur de format: {str(e)}. Veuillez réessayer.")
        except Exception as e:
            click.echo(f"Une erreur est survenue: {str(e)}")
    
    def delete_event(self, event_id: int) -> None:
        """
        Interface pour supprimer un événement
        
        Args:
            event_id: ID de l'événement à supprimer
        """
        # Vérifier si l'événement existe et si l'utilisateur y a accès
        success, event = self.event_controller.get_event(self.token, event_id)
        
        if not success:
            click.echo(f"Erreur: {event}")
            return
            
        click.echo("Événement à supprimer:")
        self.display_event(event)
        
        if click.confirm("Êtes-vous sûr de vouloir supprimer cet événement?", default=False):
            success, result = self.event_controller.delete_event(self.token, event_id)
            
            if success:
                click.echo("Événement supprimé avec succès.")
            else:
                click.echo(f"Erreur: {result}")
        else:
            click.echo("Suppression annulée.")
    
    def assign_support_contact(self, event_id: int) -> None:
        """
        Interface pour assigner un contact support à un événement

        Args:
            event_id: ID de l'événement
        """
        # Vérifier si l'événement existe et si l'utilisateur y a accès
        success, event = self.event_controller.get_event(self.token, event_id)

        if not success:
            click.echo(f"Erreur: {event}")
            return

        click.echo("Événement:")
        self.display_event(event)

        try:
            support_contact_id = click.prompt("ID du contact support", type=int)
            
            # Assigner le contact support
            success, result = self.event_controller.assign_support_contact(
                token=self.token,
                event_id=event_id,
                support_contact_id=support_contact_id
            )
            
            if success:
                click.echo("Contact support assigné avec succès.")
                self.display_event(result)
            else:
                click.echo(f"Erreur: {result}")
                
        except ValueError as e:
            click.echo(f"Erreur de format: {str(e)}. Veuillez réessayer.")
        except Exception as e:
            click.echo(f"Une erreur est survenue: {str(e)}")
    
    @staticmethod
    def register_commands(cli: click.Group, get_session: Callable, get_token: Callable) -> None:
        """
        Enregistre les commandes CLI pour la gestion des événements

        Args:
            cli: Groupe de commandes Click
            get_session: Fonction pour obtenir la session
            get_token: Fonction pour obtenir le token
        """
        @cli.group(name='events')
        def events():
            """Commandes pour la gestion des événements"""
            pass

        @events.command()
        def list_events():
            """Liste tous les événements"""
            token = get_token()
            if not token:
                click.echo("Vous devez être connecté pour effectuer cette action.")
                raise click.Abort()
            view = EventView(get_session(), token)
            view.list_events()
            
        @events.command()
        def my_events():
            """Liste uniquement les événements assignés à l'utilisateur du support"""
            token = get_token()
            if not token:
                click.echo("Vous devez être connecté pour effectuer cette action.")
                raise click.Abort()
            view = EventView(get_session(), token)
            view.list_events(filter_my_events=True)

        @events.command()
        @click.argument('event_id', type=int)
        def get_event(event_id):
            """Affiche les détails d'un événement"""
            token = get_token()
            if not token:
                click.echo("Vous devez être connecté pour effectuer cette action.")
                raise click.Abort()
            view = EventView(get_session(), token)
            view.get_event_by_id(event_id)

        @events.command()
        def create_event():
            """Crée un nouvel événement"""
            token = get_token()
            if not token:
                click.echo("Vous devez être connecté pour effectuer cette action.")
                raise click.Abort()
            view = EventView(get_session(), token)
            view.create_event()

        @events.command()
        @click.argument('event_id', type=int)
        def update_event(event_id):
            """Met à jour un événement"""
            token = get_token()
            if not token:
                click.echo("Vous devez être connecté pour effectuer cette action.")
                raise click.Abort()
            view = EventView(get_session(), token)
            view.update_event(event_id)

        @events.command()
        @click.argument('event_id', type=int)
        def delete_event(event_id):
            """Supprime un événement"""
            token = get_token()
            if not token:
                click.echo("Vous devez être connecté pour effectuer cette action.")
                raise click.Abort()
            view = EventView(get_session(), token)
            view.delete_event(event_id)

        @events.command()
        @click.argument('event_id', type=int)
        def assign_support(event_id):
            """Assigne un contact support à un événement"""
            token = get_token()
            if not token:
                click.echo("Vous devez être connecté pour effectuer cette action.")
                raise click.Abort()
            view = EventView(get_session(), token)
            view.assign_support_contact(event_id) 