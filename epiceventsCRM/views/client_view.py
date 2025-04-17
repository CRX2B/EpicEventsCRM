from typing import Any, Dict, List

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy.orm import Session

from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.models.models import Client
from epiceventsCRM.views.base_view import BaseView
from epiceventsCRM.utils.permissions import PermissionError

console = Console()


class ClientView(BaseView):
    """
    Vue pour la gestion des clients via CLI.
    """

    def __init__(self):
        """
        Initialise la vue client avec le contrôleur approprié.
        """
        super().__init__(ClientController(), "client", "clients")

    @staticmethod
    def register_commands(cli: click.Group, get_session, get_token):
        """
        Enregistre les commandes de gestion des clients.

        Args:
            cli (click.Group): Le groupe de commandes CLI
            get_session: La fonction pour obtenir une session de base de données
            get_token: La fonction pour obtenir un token JWT
        """

        @cli.group()
        def client():
            """Commandes de gestion des clients."""

        client_view = ClientView()

        # Ajout des commandes de base (liste, obtenir, supprimer)
        client.add_command(client_view.create_list_command())
        client.add_command(client_view.create_get_command())
        client.add_command(client_view.create_delete_command())

        # Ajout des commandes spécifiques

        @client.command("create")
        @click.option("--fullname", "-f", required=True, help="Nom complet du client")
        @click.option("--email", "-e", required=True, help="Email du client")
        @click.option("--phone_number", "-p", required=True, help="Téléphone du client")
        @click.option("--enterprise", "-c", required=True, help="Entreprise du client")
        @click.pass_context
        def create_client(ctx, fullname, email, phone_number, enterprise):
            """Crée un nouveau client."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return

            client_data = {
                "fullname": fullname,
                "email": email,
                "phone_number": phone_number,
                "enterprise": enterprise,
                # sales_contact_id sera automatiquement attribué dans le contrôleur
            }

            client = client_view.controller.create(token, db, client_data)

            if client:
                console.print(
                    Panel.fit(f"[bold green]Client {client.id} créé avec succès.[/bold green]")
                )
                client_view.display_item(client)
            else:
                console.print(
                    Panel.fit(
                        "[bold red]Échec de la création du client. Vérifiez vos permissions.[/bold red]"
                    )
                )

        @client.command("update")
        @click.argument("id", type=int)
        @click.option("--fullname", "-f", help="Nom complet du client")
        @click.option("--email", "-e", help="Email du client")
        @click.option("--phone_number", "-p", help="Téléphone du client")
        @click.option("--enterprise", "-c", help="Entreprise du client")
        @click.pass_context
        def update_client(ctx, id, fullname, email, phone_number, enterprise):
            """Met à jour un client existant."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return

            client_data = {}
            if fullname:
                client_data["fullname"] = fullname
            if email:
                client_data["email"] = email
            if phone_number:
                client_data["phone_number"] = phone_number
            if enterprise:
                client_data["enterprise"] = enterprise

            if not client_data:
                console.print(
                    Panel.fit("[bold yellow]Aucune donnée à mettre à jour.[/bold yellow]")
                )
                return

            try:
                client = client_view.controller.update(token, db, id, client_data)

                if client:
                    console.print(
                        Panel.fit(f"[bold green]Client {id} mis à jour avec succès.[/bold green]")
                    )
                    client_view.display_item(client)
                else:
                    # Ce cas pourrait indiquer un problème non lié à la permission si l'exception n'est pas levée
                    console.print(
                        Panel.fit(
                            f"[bold red]Échec de la mise à jour du client {id}. Vérifiez l'ID ou contactez un administrateur.[/bold red]"
                        )
                    )
            except PermissionError as e:
                # Affichage formaté de l'erreur de permission avec Rich
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\n{e.message}",
                        title="Erreur d'Autorisation",
                        border_style="red",
                    )
                )
            except Exception as e:
                # Gestion des autres erreurs potentielles
                console.print(
                    Panel.fit(
                        f"[bold red]Une erreur inattendue s'est produite lors de la mise à jour:[/bold red]\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
                    )
                )

        @client.command("my-clients")
        @click.pass_context
        def my_clients(ctx):
            """Liste mes clients (pour les commerciaux)."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(Panel.fit("[bold red]Veuillez vous connecter d'abord.[/bold red]"))
                return

            clients = client_view.controller.get_clients_by_commercial(token, db)

            if not clients:
                console.print(
                    Panel.fit("[bold yellow]Vous n'avez pas de clients assignés.[/bold yellow]")
                )
                return

            client_view.display_items(clients)

    def display_items(self, clients: List[Any]):
        """
        Affiche une liste de clients sous forme de tableau.

        Args:
            clients (List[Any]): La liste des clients à afficher
        """
        table = Table(title="Liste des clients")

        # Définition des colonnes
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Nom", style="magenta")
        table.add_column("Email", style="green")
        table.add_column("Entreprise", style="blue")
        table.add_column("Commercial", style="yellow")
        table.add_column("Créé le", style="dim")

        # Ajout des lignes
        for client in clients:
            commercial = client.sales_contact.fullname if client.sales_contact else "Non assigné"
            created = client.create_date.strftime("%d/%m/%Y") if client.create_date else "-"

            table.add_row(
                str(client.id),
                client.fullname,
                client.email,
                client.enterprise,
                commercial,
                created,
            )

        # Affichage du tableau
        console.print(table)

    def display_item(self, client: Any):
        """
        Affiche un client détaillé.

        Args:
            client (Any): Le client à afficher
        """
        table = Table(title=f"Détails du client #{client.id}")

        # Définition des colonnes
        table.add_column("Propriété", style="cyan")
        table.add_column("Valeur", style="green")

        # Ajout des informations
        commercial = client.sales_contact.fullname if client.sales_contact else "Non assigné"

        # Formatage des dates
        create_date = (
            client.create_date.strftime("%d/%m/%Y %H:%M") if client.create_date else "Non définie"
        )
        update_date = (
            client.update_date.strftime("%d/%m/%Y %H:%M") if client.update_date else "Non définie"
        )

        table.add_row("ID", str(client.id))
        table.add_row("Nom complet", client.fullname)
        table.add_row("Email", client.email)
        table.add_row("Téléphone", str(client.phone_number))
        table.add_row("Entreprise", client.enterprise)
        table.add_row("Commercial", commercial)
        table.add_row("Date de création", create_date)
        table.add_row("Dernière mise à jour", update_date)

        # Affichage du tableau
        console.print(table)
