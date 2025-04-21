from typing import Any, List
import math

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.views.base_view import BaseView
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

        @event.command("list-events")
        @click.option("--page", type=int, default=1, help="Numéro de la page")
        @click.option("--page-size", type=int, default=10, help="Nombre d'éléments par page")
        @click.option(
            "--no-support",
            is_flag=True,
            default=False,
            help="Affiche uniquement les événements sans support assigné.",
        )
        @click.pass_context
        def list_events(ctx, page, page_size, no_support):
            """Liste les événements avec pagination et filtre optionnel."""
            db: Session = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]", border_style="red"
                    )
                )
                return

            if page < 1 or page_size < 1:
                console.print(
                    Panel.fit(
                        "[bold red]Page et taille de page doivent être >= 1.[/bold red]",
                        border_style="red",
                    )
                )
                return

            try:
                items, total = event_view.controller.get_all(
                    token, db, page=page, page_size=page_size, no_support_only=no_support
                )

                if not items:
                    msg = "Aucun événement trouvé."
                    if no_support:
                        msg = "Aucun événement trouvé sans support assigné."
                    console.print(
                        Panel.fit(f"[bold yellow]{msg}[/bold yellow]", border_style="yellow")
                    )
                    return

                total_pages = math.ceil(total / page_size)
                console.print(
                    f"\n[bold]Page {page} sur {total_pages}[/bold] - Total filtré: {total} événements"
                )
                console.print(
                    f"Affichage des éléments {((page - 1) * page_size) + 1} à {min(page * page_size, total)}"
                )

                event_view.display_items(items)

                if total_pages > 1:
                    console.print("\n[bold]Navigation:[/bold]")
                    options = f"{' --no-support' if no_support else ''}"
                    if page > 1:
                        console.print(f"  Page précédente: list-events --page {page - 1}{options}")
                    if page < total_pages:
                        console.print(f"  Page suivante:   list-events --page {page + 1}{options}")
                    console.print(f"  Changer taille:  list-events --page-size <nombre>{options}")

            except PermissionError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\n{e.message}",
                        title="Erreur",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la récupération des événements:[/bold red]\n{str(e)}",
                        border_style="red",
                    )
                )

        event.add_command(event_view.create_get_command())
        event.add_command(event_view.create_delete_command())

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
                            "[bold red]Échec de la création de l'événement (raison inconnue).[/bold red]",
                            border_style="red",
                        )
                    )
            except (PermissionError, ValueError, IntegrityError) as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Échec de la création:[/bold red]\n{e}",
                        title="Erreur",
                        border_style="red",
                    )
                )
            except Exception as e:
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
            client_info = event.get_client_info()
            client_name = client_info["name"] if client_info else "Non disponible"

            start_date = (
                event.start_event.strftime("%d/%m/%Y %H:%M") if event.start_event else "N/A"
            )
            end_date = event.end_event.strftime("%d/%m/%Y %H:%M") if event.end_event else "N/A"

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

        table.add_column("Propriété", style="cyan")
        table.add_column("Valeur", style="green")

        client_info = event.get_client_info()
        client_name = client_info["name"] if client_info else "Non disponible"
        client_email = client_info["email"] if client_info else "Non disponible"
        client_phone = client_info["phone"] if client_info else "Non disponible"

        start_date = (
            event.start_event.strftime("%d/%m/%Y %H:%M") if event.start_event else "Non définie"
        )
        end_date = event.end_event.strftime("%d/%m/%Y %H:%M") if event.end_event else "Non définie"

        support_name = event.support_contact.fullname if event.support_contact else "Non assigné"

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

        console.print(table)
