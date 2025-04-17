from typing import Any, List

import click
from rich.panel import Panel
from rich.table import Table

from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.views.base_view import BaseView, console
from epiceventsCRM.utils.permissions import PermissionError


class ContractView(BaseView):
    """
    Vue pour la gestion des contrats via CLI.
    """

    def __init__(self):
        """
        Initialise la vue des contrats.
        """
        super().__init__(ContractController(), "contract", "contracts")

    @staticmethod
    def register_commands(cli: click.Group, get_session, get_token):
        """
        Enregistre les commandes de gestion des contrats.

        Args:
            cli (click.Group): Le groupe de commandes CLI
            get_session: La fonction pour obtenir une session de base de données
            get_token: La fonction pour obtenir un token JWT
        """

        @cli.group()
        def contract():
            """Commandes de gestion des contrats."""

        contract_view = ContractView()

        # Ajout des commandes de base (liste, obtenir, supprimer)
        contract.add_command(contract_view.create_list_command())
        contract.add_command(contract_view.create_get_command())
        contract.add_command(contract_view.create_delete_command())

        # Ajout des commandes spécifiques

        @contract.command("create")
        @click.option("--client", "-c", required=True, type=int, help="ID du client")
        @click.option("--amount", "-a", required=True, type=float, help="Montant du contrat")
        @click.option("--signed", "-s", is_flag=True, help="Contrat signé")
        @click.pass_context
        def create_contract(ctx, client, amount, signed):
            """Crée un nouveau contrat."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]", border_style="red"
                    )
                )
                return

            # Préparer le dictionnaire de données pour le contrôleur
            contract_data = {
                "client_id": client,
                "amount": amount,
                "status": signed,
            }

            try:
                created_contract = contract_view.controller.create(
                    token=token, db=db, data=contract_data
                )

                if created_contract:
                    console.print(
                        Panel.fit(
                            f"[bold green]Contrat {created_contract.id} créé avec succès.[/bold green]",
                            border_style="green",
                        )
                    )
                    contract_view.display_item(created_contract)
                else:
                    # L'échec peut être dû à une permission refusée (levée par le décorateur)
                    # ou à une autre erreur (client non trouvé, commercial manquant, etc.)
                    # Le contrôleur log les détails avec Sentry/capture_message
                    console.print(
                        Panel.fit(
                            f"[bold red]Échec de la création du contrat.[/bold red]\nVérifiez les informations fournies (ID client) et vos permissions.",
                            title="Erreur de Création",
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
            except (
                ValueError
            ) as e:  # Capturer les erreurs de valeur potentielles (ex: client non trouvé)
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur de données:[/bold red]\n{str(e)}",
                        title="Erreur de Création",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur inattendue lors de la création :[/bold red]\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
                    )
                )

        @contract.command("update")
        @click.argument("id", type=int)
        @click.option("--amount", "-a", type=float, help="Montant du contrat")
        @click.option("--remaining-amount", "-r", type=float, help="Montant restant du contrat")
        @click.option(
            "--signed/--unsigned",
            "status",
            is_flag=True,
            default=None,
            help="Statut signé du contrat",
        )
        @click.pass_context
        def update_contract(ctx, id, amount, remaining_amount, status):
            """Met à jour un contrat existant."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]", border_style="red"
                    )
                )
                return

            if amount is None and remaining_amount is None and status is None:
                console.print(
                    Panel.fit(
                        "[bold yellow]Aucune donnée à mettre à jour.[/bold yellow]",
                        border_style="yellow",
                    )
                )
                return

            update_data = {}
            if amount is not None:
                update_data["amount"] = amount
            if remaining_amount is not None:
                update_data["remaining_amount"] = remaining_amount
            if status is not None:
                update_data["status"] = status

            try:
                contract = contract_view.controller.update_contract(token, db, id, update_data)
                if contract:
                    console.print(
                        Panel.fit(
                            f"[bold green]Contrat {id} mis à jour avec succès.[/bold green]",
                            border_style="green",
                        )
                    )
                    contract_view.display_item(contract)
                else:
                    console.print(
                        Panel.fit(
                            f"[bold red]Échec de la mise à jour du contrat {id}. Vérifiez l'ID et vos permissions.[/bold red]",
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

        @contract.command("by-client")
        @click.argument("client_id", type=int)
        @click.pass_context
        def contracts_by_client(ctx, client_id):
            """Liste les contrats d'un client."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]", border_style="red"
                    )
                )
                return

            contracts = contract_view.controller.get_contracts_by_client(token, db, client_id)

            if not contracts:
                console.print(
                    Panel.fit(
                        f"[bold yellow]Aucun contrat trouvé pour le client {client_id}.[/bold yellow]",
                        border_style="yellow",
                    )
                )
                return

            contract_view.display_items(contracts)

        @contract.command("my-contracts")
        @click.pass_context
        def my_contracts(ctx):
            """Liste les contrats des clients dont je suis le commercial."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]", border_style="red"
                    )
                )
                return

            contracts = contract_view.controller.get_contracts_by_commercial(token, db)

            if not contracts:
                console.print(
                    Panel.fit(
                        "[bold yellow]Vous n'avez pas de contrats associés.[/bold yellow]",
                        border_style="yellow",
                    )
                )
                return

            contract_view.display_items(contracts)

    def display_items(self, contracts: List[Any]):
        """
        Affiche une liste de contrats sous forme de tableau avec Rich.

        Args:
            contracts (List[Any]): La liste des contrats à afficher
        """
        table = Table(title="Liste des Contrats", show_header=True, header_style="bold cyan")

        # Définition des colonnes
        table.add_column("ID", style="dim", justify="center")
        table.add_column("Client", style="green")
        table.add_column("Montant", justify="right", style="yellow")
        table.add_column("Restant", justify="right", style="yellow")
        table.add_column("Statut", justify="center")
        table.add_column("Commercial", style="green")

        # Ajout des lignes
        for contract in contracts:
            client_name = contract.client.fullname if contract.client else "N/A"
            commercial = contract.sales_contact.fullname if contract.sales_contact else "N/A"

            # Statut avec couleur spécifique
            status = "[green]Signé[/green]" if contract.status else "[red]Non signé[/red]"

            table.add_row(
                str(contract.id),
                client_name,
                f"{contract.amount} €",
                f"{contract.remaining_amount} €",
                status,
                commercial,
            )

        # Affichage du tableau
        console.print(table)

    def display_item(self, contract: Any):
        """
        Affiche un contrat détaillé avec Rich.

        Args:
            contract (Any): Le contrat à afficher
        """
        try:
            # Création d'un tableau pour les informations de base
            contract_info = Table(show_header=False, box=None)
            contract_info.add_column("Propriété", style="cyan")
            contract_info.add_column("Valeur")

            # Ajout des informations de base du contrat
            contract_info.add_row("ID", str(contract.id))
            contract_info.add_row("Montant total", f"{contract.amount} €")
            contract_info.add_row("Montant restant", f"{contract.remaining_amount} €")

            # Statut avec couleur spécifique
            status_value = "[green]Signé[/green]" if contract.status else "[red]Non signé[/red]"
            contract_info.add_row("Statut", status_value)

            if hasattr(contract, "create_date") and contract.create_date:
                date_formatted = contract.create_date.strftime("%Y-%m-%d %H:%M:%S")
                contract_info.add_row("Date de création", date_formatted)

            if hasattr(contract, "updated_date") and contract.updated_date:
                date_formatted = contract.updated_date.strftime("%Y-%m-%d %H:%M:%S")
                contract_info.add_row("Dernière mise à jour", date_formatted)

            # Obtenir les détails du client et du commercial
            from epiceventsCRM.database import get_session as get_db_session

            db = get_db_session()

            try:
                # Récupérer les informations du client
                from epiceventsCRM.models.models import Client, User

                client = db.query(Client).filter(Client.id == contract.client_id).first()
                if client:
                    contract_info.add_row("Client ID", str(contract.client_id))
                    contract_info.add_row("Client", f"[green]{client.fullname}[/green]")

                # Récupérer les informations du commercial
                commercial = db.query(User).filter(User.id == contract.sales_contact_id).first()
                if commercial:
                    contract_info.add_row("Commercial ID", str(contract.sales_contact_id))
                    contract_info.add_row("Commercial", f"[green]{commercial.fullname}[/green]")

            finally:
                db.close()

            # Affichage des informations.
            panel = Panel(
                contract_info,
                title=f"[bold yellow]Contrat #{contract.id}[/bold yellow]",
                border_style="yellow",
            )
            console.print(panel)

        except Exception as e:
            console.print(f"[bold red]Erreur lors de l'affichage du contrat:[/bold red] {str(e)}")
