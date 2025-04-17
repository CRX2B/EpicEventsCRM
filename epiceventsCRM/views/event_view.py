from typing import Any, List, Callable

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy.exc import IntegrityError

from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.views.base_view import BaseView
from epiceventsCRM.utils.auth import verify_token
from epiceventsCRM.utils.permissions import PermissionError


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

            try:
                event = event_view.controller.create(token, db, event_data)

                # Si l'événement est retourné (pas d'exception), c'est un succès
                if event:
                    console.print(
                        Panel.fit(
                            f"[bold green]Événement {event.id} créé avec succès.[/bold green]"
                        )
                    )
                    event_view.display_item(event)
                else:
                    console.print(
                        Panel.fit(
                            f"[bold red]Échec de la création de l'événement (raison inconnue).[/bold red]",
                            border_style="red",
                        )
                    )
            except (PermissionError, ValueError, IntegrityError) as e:
                # Capturer les erreurs spécifiques attendues (Permission, Données invalides, Contrainte BDD)
                console.print(
                    Panel.fit(
                        f"[bold red]Échec de la création:[/bold red]\n{e}",  # Afficher directement le message de l'exception
                        title="Erreur",
                        border_style="red",
                    )
                )
            except Exception as e:
                # Capturer toute autre exception inattendue
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la création :[/bold red]\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
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
            if notes is not None:
                event_data["notes"] = notes

            if not event_data:
                console.print(
                    Panel.fit("[bold yellow]Aucune donnée à mettre à jour.[/bold yellow]")
                )
                return

            try:
                event = event_view.controller.update(token, db, id, event_data)
                if event:
                    console.print(
                        Panel.fit(
                            f"[bold green]Événement {id} mis à jour avec succès.[/bold green]"
                        )
                    )
                    event_view.display_item(event)
                else:
                    console.print(
                        Panel.fit(
                            f"[bold red]Échec de la mise à jour de l'événement {id}. Vérifiez l'ID et vos permissions.[/bold red]",
                            border_style="red",
                        )
                    )
            except PermissionError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\n{e.message}",
                        title="Erreur d'Autorisation",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la mise à jour :[/bold red]\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
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

            try:
                updated_event = event_view.controller.update_event_notes(token, db, id, notes)

                if updated_event:
                    console.print(
                        Panel.fit(
                            f"[bold green]Notes de l'événement {id} mises à jour avec succès.[/bold green]"
                        )
                    )
                    console.print(f"[bold]Nouvelles notes:[/bold] {updated_event.notes}")
                else:
                    console.print(
                        Panel.fit(
                            f"[bold red]Échec de la mise à jour des notes de l'événement {id}. Événement non trouvé ?[/bold red]",
                            border_style="red",
                        )
                    )
            except PermissionError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\n{e.message}",
                        title="Erreur d'Autorisation",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la mise à jour des notes :[/bold red]\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
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

            try:
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
                            f"[bold red]Échec de l'assignation du contact support à l'événement {id}. Vérifiez les IDs et vos permissions.[/bold red]",
                            border_style="red",
                        )
                    )
            except PermissionError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\n{e.message}",
                        title="Erreur d'Autorisation",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de l'assignation du support :[/bold red]\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
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
            """Liste les événements assignés au support connecté."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return

            try:
                events = event_view.controller.get_events_by_support(token, db)

                if not events:
                    console.print(
                        Panel.fit(
                            "[bold yellow]Aucun événement ne vous est assigné.[/bold yellow]",
                            border_style="yellow",
                        )
                    )
                else:
                    event_view.display_items(events)

            except PermissionError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\n{e.message}",
                        title="Erreur d'Autorisation",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la récupération des événements :[/bold red]\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
                    )
                )

    def display_items(self, events: List[Any]):
        """
        Affiche une liste d'événements sous forme de tableau avec Rich.

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
