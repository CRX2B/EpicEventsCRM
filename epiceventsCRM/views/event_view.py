from typing import Any, List, Callable

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

        event_view = EventView()

        # Ajout des commandes de base (liste, obtenir, supprimer)
        event.add_command(event_view.create_list_command())
        event.add_command(event_view.create_get_command())
        event.add_command(event_view.create_delete_command())

        # Ajout des commandes spécifiques

        @event.command("create")
        @click.option("--contract", "-c", required=True, type=int, help="ID du contrat")
        @click.option("--name", "-n", required=True, help="Nom de l'événement")
        @click.option(
            "--start-date", "-s", required=True, help="Date et heure de début (YYYY-MM-DD HH:MM)"
        )
        @click.option(
            "--end-date", "-e", required=True, help="Date et heure de fin (YYYY-MM-DD HH:MM)"
        )
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
                "notes": notes or "",
            }

            event = event_view.controller.create(token, db, event_data)

            if event:
                console.print(
                    Panel.fit(f"[bold green]Événement {event.id} créé avec succès.[/bold green]")
                )
                event_view.display_item(event)
            else:
                console.print(
                    Panel.fit(
                        "[bold red]Échec de la création de l'événement. Vérifiez vos permissions.[/bold red]"
                    )
                )

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
                console.print(
                    Panel.fit("[bold yellow]Aucune donnée à mettre à jour.[/bold yellow]")
                )
                return

            event = event_view.controller.update(token, db, id, event_data)

            if event:
                console.print(
                    Panel.fit(f"[bold green]Événement {id} mis à jour avec succès.[/bold green]")
                )
                event_view.display_item(event)
            else:
                console.print(
                    Panel.fit(
                        f"[bold red]Échec de la mise à jour de l'événement {id}. Vérifiez l'ID et vos permissions.[/bold red]"
                    )
                )

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
                console.print(
                    Panel.fit(
                        f"[bold green]Notes de l'événement {id} mises à jour avec succès.[/bold green]"
                    )
                )
                console.print(f"[bold]Nouvelles notes:[/bold] {event.notes}")
            else:
                console.print(
                    Panel.fit(
                        f"[bold red]Échec de la mise à jour des notes de l'événement {id}. Vérifiez l'ID et vos permissions.[/bold red]"
                    )
                )

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
                console.print(
                    Panel.fit(
                        f"[bold green]Contact support {support_id} assigné à l'événement {id} avec succès.[/bold green]"
                    )
                )
                event_view.display_item(event)
            else:
                console.print(
                    Panel.fit(
                        f"[bold red]Échec de l'assignation du contact support à l'événement {id}. Vérifiez les IDs et vos permissions.[/bold red]"
                    )
                )

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
                console.print(
                    Panel.fit(
                        f"[bold yellow]Aucun événement trouvé pour le contrat {contract_id}.[/bold yellow]"
                    )
                )
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
                console.print(
                    Panel.fit("[bold yellow]Vous n'êtes assigné à aucun événement.[/bold yellow]")
                )
                return

            event_view.display_items(events)

        @event.command("delete-event")
        @click.argument("id", type=int)
        @click.confirmation_option(prompt="Êtes-vous sûr de vouloir supprimer ce event ?")
        @click.pass_context
        def delete_event(ctx, id):
            """Supprime un événement."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]",
                        border_style="red"
                    )
                )
                return

            try:
                # Vérifier si l'événement existe
                event = event_view.controller.get_event(token, db, id)
                if not event:
                    console.print(
                        Panel.fit(
                            f"[bold red]L'événement {id} n'existe pas ou vous n'avez pas les permissions pour y accéder.[/bold red]",
                            border_style="red"
                        )
                    )
                    return

                # Tenter la suppression
                success = event_view.controller.delete_event(token, db, id)

                if success:
                    console.print(
                        Panel.fit(
                            f"[bold green]Événement {id} supprimé avec succès.[/bold green]",
                            border_style="green"
                        )
                    )
                else:
                    # Message d'erreur détaillé selon le département
                    payload = decode_token(token)
                    department = payload.get("department", "").lower() if payload else ""
                    
                    error_message = f"[bold red]Échec de la suppression de l'événement {id}.[/bold red]\n\n"
                    
                    if department == "commercial":
                        error_message += "[red]• Vous êtes membre du département commercial[/red]\n"
                        error_message += "[red]• Seuls les membres du département gestion peuvent supprimer des événements[/red]"
                    elif department == "support":
                        error_message += "[red]• Vous êtes membre du département support[/red]\n"
                        error_message += "[red]• Seuls les membres du département gestion peuvent supprimer des événements[/red]"
                    else:
                        error_message += "[red]• Vous n'avez pas les permissions nécessaires pour supprimer des événements[/red]"
                    
                    console.print(
                        Panel.fit(
                            error_message,
                            border_style="red"
                        )
                    )

            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Une erreur inattendue s'est produite :[/bold red]\n{str(e)}",
                        border_style="red"
                    )
                )

    def display_items(self, events: List[Any]):
        """
        Affiche une liste d'événements.

        Args:
            events (List[Any]): La liste des événements à afficher
        """
        if not events:
            console.print("[yellow]Aucun événement trouvé.[/yellow]")
            return

        table = Table(title="Liste des événements")
        table.add_column("ID", style="cyan")
        table.add_column("Nom", style="green")
        table.add_column("Client", style="blue")
        table.add_column("Date début", style="magenta")
        table.add_column("Date fin", style="magenta")
        table.add_column("Lieu", style="yellow")
        table.add_column("Support", style="red")

        for event in events:
            # Récupération des informations client
            client_info = event.get_client_info()
            client_name = client_info["name"] if client_info else "Non disponible"

            # Formatage des dates
            start_date = (
                event.start_event.strftime("%d/%m/%Y %H:%M") if event.start_event else "N/A"
            )
            end_date = event.end_event.strftime("%d/%m/%Y %H:%M") if event.end_event else "N/A"

            # Récupération du nom du support
            support_name = (
                event.support_contact.fullname if event.support_contact else "Non assigné"
            )

            table.add_row(
                str(event.id),
                event.name,
                client_name,
                start_date,
                end_date,
                event.location,
                support_name,
            )

        console.print(table)

    def display_item(self, event: Any):
        """
        Affiche les détails d'un événement.

        Args:
            event (Any): L'événement à afficher
        """
        table = Table(title=f"Détails de l'événement #{event.id}")

        # Définition des colonnes
        table.add_column("Propriété", style="cyan")
        table.add_column("Valeur", style="green")

        # Récupération des informations client
        client_info = event.get_client_info()
        client_name = client_info["name"] if client_info else "Non disponible"
        client_email = client_info["email"] if client_info else "Non disponible"
        client_phone = client_info["phone"] if client_info else "Non disponible"

        # Formatage des dates
        start_date = (
            event.start_event.strftime("%d/%m/%Y %H:%M") if event.start_event else "Non définie"
        )
        end_date = event.end_event.strftime("%d/%m/%Y %H:%M") if event.end_event else "Non définie"

        # Récupération du nom du support
        support_name = event.support_contact.fullname if event.support_contact else "Non assigné"

        # Ajout des informations
        table.add_row("ID", str(event.id))
        table.add_row("Nom", event.name)
        table.add_row("Contrat ID", str(event.contract_id))
        table.add_row("Client", client_name)
        table.add_row("Email client", client_email)
        table.add_row("Téléphone client", str(client_phone))
        table.add_row("Date de début", start_date)
        table.add_row("Date de fin", end_date)
        table.add_row("Lieu", event.location)
        table.add_row("Contact support", support_name)
        table.add_row("Participants", str(event.attendees))
        table.add_row("Notes", event.notes or "Aucune note")

        # Affichage du tableau
        console.print(table)

    def create_get_command(self) -> Callable:
        """
        Crée une commande pour obtenir un événement par son ID.

        Returns:
            Callable: La fonction de commande
        """

        @click.command(f"get-{self.entity_name}")
        @click.argument("id", type=int)
        @click.pass_context
        def get_item(ctx, id):
            """Obtient un événement par son ID."""
            db = ctx.obj["get_session"]()
            token = ctx.obj["get_token"]()

            # Vérifier si l'utilisateur est connecté
            if not token:
                console.print(
                    Panel.fit(
                        f"[bold red]Vous devez être connecté pour voir un {self.entity_name}.[/bold red]\n"
                        f"[red]Utilisez la commande 'auth login' pour vous connecter.[/red]",
                        border_style="red",
                    )
                )
                return

            try:
                item = self.controller.get_event(token, db, id)

                if not item:
                    console.print(
                        Panel.fit(
                            f"[bold red]{self.entity_name.capitalize()} {id} non trouvé.[/bold red]",
                            border_style="red",
                        )
                    )
                    return

                self.display_item(item)
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la récupération du {self.entity_name} {id}:[/bold red]\n"
                        f"[red]{str(e)}[/red]",
                        border_style="red",
                    )
                )

        return get_item
