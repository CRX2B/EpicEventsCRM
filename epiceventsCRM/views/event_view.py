import click
from typing import List, Any, Dict
import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.views.base_view import BaseView

# Création d'une instance de console Rich pour l'affichage
console = Console()

class EventView(BaseView):
    """
    Vue pour la gestion des événements via CLI.
    """
    
    def __init__(self):
        """
        Initialise la vue événement avec le contrôleur approprié.
        """
        super().__init__(EventController(), "event", "events")
    
    @staticmethod
    def register_commands(cli: click.Group, get_session, get_token):
        """
        Enregistre les commandes de gestion des événements.
        
        Args:
            cli (click.Group): Le groupe de commandes CLI
            get_session: La fonction pour obtenir une session de base de données
            get_token: La fonction pour obtenir un token JWT
        """
        @cli.group()
        def event():
            """Commandes de gestion des événements."""
            pass
        
        event_view = EventView()
        
        # Ajout des commandes de base (liste, obtenir, supprimer)
        event.add_command(event_view.create_list_command())
        event.add_command(event_view.create_get_command())
        event.add_command(event_view.create_delete_command())
        
        # Ajout des commandes spécifiques
        
        @event.command("create")
        @click.option("--contract", "-c", required=True, type=int, help="ID du contrat")
        @click.option("--name", "-n", required=True, help="Nom de l'événement")
        @click.option("--start-date", "-s", required=True, help="Date et heure de début (YYYY-MM-DD HH:MM)")
        @click.option("--end-date", "-e", required=True, help="Date et heure de fin (YYYY-MM-DD HH:MM)")
        @click.option("--location", "-l", required=True, help="Lieu de l'événement")
        @click.option("--attendees", "-a", type=int, required=True, help="Nombre de participants")
        @click.option("--notes", help="Notes sur l'événement")
        @click.pass_context
        def create_event(ctx, contract, name, start_date, end_date, location, attendees, notes):
            """Crée un nouvel événement."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return
            
            event_data = {
                "contract_id": contract,
                "name": name,
                "start_event": start_date,
                "end_event": end_date,
                "location": location,
                "attendees": attendees,
                "notes": notes or ""
            }
            
            event = event_view.controller.create(token, db, event_data)
            
            if event:
                console.print(Panel.fit(f"[bold green]Événement {event.id} créé avec succès.[/bold green]"))
                event_view.display_item(event)
            else:
                console.print(Panel.fit("[bold red]Échec de la création de l'événement. Vérifiez vos permissions.[/bold red]"))
        
        @event.command("update")
        @click.argument("id", type=int)
        @click.option("--name", "-n", help="Nom de l'événement")
        @click.option("--start-date", "-s", help="Date et heure de début (YYYY-MM-DD HH:MM)")
        @click.option("--end-date", "-e", help="Date et heure de fin (YYYY-MM-DD HH:MM)")
        @click.option("--location", "-l", help="Lieu de l'événement")
        @click.option("--attendees", "-a", type=int, help="Nombre de participants")
        @click.option("--notes", help="Notes sur l'événement")
        @click.pass_context
        def update_event(ctx, id, name, start_date, end_date, location, attendees, notes):
            """Met à jour un événement existant."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return
            
            event_data = {}
            if name:
                event_data["name"] = name
            if start_date:
                event_data["start_event"] = start_date
            if end_date:
                event_data["end_event"] = end_date
            if location:
                event_data["location"] = location
            if attendees:
                event_data["attendees"] = attendees
            if notes is not None:  # Permettre de vider les notes
                event_data["notes"] = notes
            
            if not event_data:
                console.print(Panel.fit("[bold yellow]Aucune donnée à mettre à jour.[/bold yellow]"))
                return
            
            event = event_view.controller.update(token, db, id, event_data)
            
            if event:
                console.print(Panel.fit(f"[bold green]Événement {id} mis à jour avec succès.[/bold green]"))
                event_view.display_item(event)
            else:
                console.print(Panel.fit(f"[bold red]Échec de la mise à jour de l'événement {id}. Vérifiez l'ID et vos permissions.[/bold red]"))
        
        @event.command("update-notes")
        @click.argument("id", type=int)
        @click.argument("notes")
        @click.pass_context
        def update_notes(ctx, id, notes):
            """Met à jour les notes d'un événement (pour le support)."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return
            
            event = event_view.controller.update_event_notes(token, db, id, notes)
            
            if event:
                console.print(Panel.fit(f"[bold green]Notes de l'événement {id} mises à jour avec succès.[/bold green]"))
                console.print(f"[bold]Nouvelles notes:[/bold] {event.notes}")
            else:
                console.print(Panel.fit(f"[bold red]Échec de la mise à jour des notes de l'événement {id}. Vérifiez l'ID et vos permissions.[/bold red]"))
        
        @event.command("assign-support")
        @click.argument("id", type=int)
        @click.argument("support_id", type=int)
        @click.pass_context
        def assign_support(ctx, id, support_id):
            """Assigne un contact support à un événement (pour la gestion)."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return
            
            event = event_view.controller.update_event_support(token, db, id, support_id)
            
            if event:
                console.print(Panel.fit(f"[bold green]Contact support {support_id} assigné à l'événement {id} avec succès.[/bold green]"))
                event_view.display_item(event)
            else:
                console.print(Panel.fit(f"[bold red]Échec de l'assignation du contact support à l'événement {id}. Vérifiez les IDs et vos permissions.[/bold red]"))
        
        @event.command("by-contract")
        @click.argument("contract_id", type=int)
        @click.pass_context
        def events_by_contract(ctx, contract_id):
            """Liste les événements d'un contrat."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return
            
            events = event_view.controller.get_events_by_contract(token, db, contract_id)
            
            if not events:
                console.print(Panel.fit(f"[bold yellow]Aucun événement trouvé pour le contrat {contract_id}.[/bold yellow]"))
                return
                
            event_view.display_items(events)
        
        @event.command("my-events")
        @click.pass_context
        def my_events(ctx):
            """Liste les événements dont je suis le support (pour le support)."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return
            
            events = event_view.controller.get_events_by_support(token, db)
            
            if not events:
                console.print(Panel.fit("[bold yellow]Vous n'êtes assigné à aucun événement.[/bold yellow]"))
                return
                
            event_view.display_items(events)
    
    def display_items(self, events: List[Any]):
        """
        Affiche une liste d'événements sous forme de tableau.
        
        Args:
            events (List[Any]): La liste des événements à afficher
        """
        table = Table(title="Liste des événements")
        
        # Définition des colonnes
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Nom", style="magenta")
        table.add_column("Client", style="green")
        table.add_column("Début", style="blue")
        table.add_column("Fin", style="blue")
        table.add_column("Lieu", style="yellow")
        table.add_column("Support", style="dim")
        
        # Ajout des lignes
        for event in events:
            client_name = event.client_name if event.client_name else "Non disponible"
            support = event.support_contact.fullname if event.support_contact else "Non assigné"
            
            start_date = event.start_event.strftime("%d/%m/%Y %H:%M") if event.start_event else "-"
            end_date = event.end_event.strftime("%d/%m/%Y %H:%M") if event.end_event else "-"
            
            table.add_row(
                str(event.id),
                event.name,
                client_name,
                start_date,
                end_date,
                event.location,
                support
            )
        
        # Affichage du tableau
        console.print(table)
    
    def display_item(self, event: Any):
        """
        Affiche un événement détaillé.
        
        Args:
            event (Any): L'événement à afficher
        """
        table = Table(title=f"Détails de l'événement #{event.id}")
        
        # Définition des colonnes
        table.add_column("Propriété", style="cyan")
        table.add_column("Valeur", style="green")
        
        # Récupérer les informations du client à partir des nouveaux champs
        client_name = event.client_name if event.client_name else "Non disponible"
        client_contact = event.client_contact if event.client_contact else "Non disponible"
        support = event.support_contact.fullname if event.support_contact else "Non assigné"
        
        # Formatage des dates
        start_date = event.start_event.strftime("%d/%m/%Y %H:%M") if event.start_event else "Non définie"
        end_date = event.end_event.strftime("%d/%m/%Y %H:%M") if event.end_event else "Non définie"
        updated_date = event.updated_date.strftime("%d/%m/%Y %H:%M") if hasattr(event, 'updated_date') and event.updated_date else "Non définie"
        
        # Ajout des données
        table.add_row("ID", str(event.id))
        table.add_row("Nom", event.name)
        table.add_row("Client", client_name)
        table.add_row("Contact client", client_contact)
        table.add_row("Contrat", str(event.contract_id))
        table.add_row("Date de début", start_date)
        table.add_row("Date de fin", end_date)
        table.add_row("Lieu", event.location)
        table.add_row("Participants", str(event.attendees))
        table.add_row("Contact support", support)
        
        if event.notes:
            table.add_row("Notes", event.notes)
        
        if hasattr(event, 'updated_date') and event.updated_date:
            table.add_row("Dernière mise à jour", updated_date)
        
        # Affichage du tableau
        console.print(table) 