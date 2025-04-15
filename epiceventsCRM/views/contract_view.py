from typing import Any, List

import click
from rich.panel import Panel
from rich.table import Table

from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.views.base_view import BaseView, console


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

            success, result = contract_view.controller.create_contract(
                token, db, client, amount, signed
            )

            if success:
                console.print(
                    Panel.fit(
                        f"[bold green]Contrat {result.id} créé avec succès.[/bold green]",
                        border_style="green",
                    )
                )
                contract_view.display_item(result)
            else:
                console.print(
                    Panel.fit(
                        f"[bold red]Échec de la création du contrat: {result}[/bold red]",
                        border_style="red",
                    )
                )

        @contract.command("update")
        @click.argument("id", type=int)
        @click.option("--amount", "-a", type=float, help="Montant du contrat")
        @click.option("--remaining-amount", "-r", type=float, help="Montant restant du contrat")
        @click.option("--signed/--unsigned", is_flag=True, default=None, help="Statut signé du contrat")
        @click.pass_context
        def update_contract(ctx, id, amount, remaining_amount, signed):
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

            # Vérifier qu'au moins une option est fournie
            if amount is None and remaining_amount is None and signed is None:
                console.print(
                    Panel.fit(
                        "[bold yellow]Veuillez spécifier au moins une valeur à mettre à jour (montant, montant restant ou statut).[/bold yellow]",
                        border_style="yellow",
                    )
                )
                return

            # Préparer les données de mise à jour
            update_data = {}
            if amount is not None:
                update_data["amount"] = amount
            if remaining_amount is not None:
                update_data["remaining_amount"] = remaining_amount
            if signed is not None:
                update_data["status"] = signed

            # Effectuer la mise à jour
            contract = contract_view.controller.update_contract(token, db, id, update_data)
            if contract:
                # Afficher les messages de succès pour chaque mise à jour effectuée
                if "amount" in update_data:
                    console.print(
                        Panel.fit(
                            f"[bold green]Montant du contrat {id} mis à jour avec succès: {amount}.[/bold green]",
                            border_style="green",
                        )
                    )
                if "remaining_amount" in update_data:
                    console.print(
                        Panel.fit(
                            f"[bold green]Montant restant du contrat {id} mis à jour avec succès: {remaining_amount}.[/bold green]",
                            border_style="green",
                        )
                    )
                if "status" in update_data:
                    status_txt = "signé" if signed else "non signé"
                    console.print(
                        Panel.fit(
                            f"[bold green]Statut du contrat {id} mis à jour avec succès: {status_txt}.[/bold green]",
                            border_style="green",
                        )
                    )
            else:
                # Récupération des informations pour un message plus détaillé
                from epiceventsCRM.database import get_session as get_db_session
                from epiceventsCRM.models.models import Contract, User
                from epiceventsCRM.utils.token_manager import decode_token

                # Message d'erreur détaillé
                error_message = f"[bold red]Échec de la mise à jour du contrat {id}.[/bold red]\n\n"

                try:
                    db_local = get_db_session()
                    payload = decode_token(token)

                    # Vérifier si le token est valide
                    if not payload or "sub" not in payload or "department" not in payload:
                        error_message += "[red]Token invalide ou informations manquantes[/red]"
                    else:
                        user_id = payload["sub"]
                        department = payload["department"]

                        # Récupérer les informations du contrat
                        contract_obj = db_local.query(Contract).filter(Contract.id == id).first()

                        if not contract_obj:
                            error_message += f"[red]Le contrat {id} n'existe pas.[/red]"
                        else:
                            # Récupérer le nom de l'utilisateur
                            user = db_local.query(User).filter(User.id == user_id).first()
                            user_name = user.fullname if user else f"ID: {user_id}"

                            # Récupérer le commercial associé au contrat
                            contract_commercial = (
                                db_local.query(User)
                                .filter(User.id == contract_obj.sales_contact_id)
                                .first()
                            )
                            commercial_name = (
                                contract_commercial.fullname if contract_commercial else "inconnu"
                            )

                            # Explication selon le département
                            if department.lower() == "commercial":
                                if contract_obj.sales_contact_id != user_id:
                                    error_message += f"[red]Vous ({user_name}) n'êtes pas le commercial associé à ce contrat.[/red]\n"
                                    error_message += f"[red]Seul le commercial associé ({commercial_name}) ou un membre du département gestion peut modifier ce contrat.[/red]"
                                else:
                                    error_message += "[red]Une erreur inconnue s'est produite. Cette action a été signalée.[/red]"
                            else:
                                error_message += f"[red]Votre département ({department}) n'a pas les permissions nécessaires pour cette action.[/red]\n"
                                error_message += "[red]Seuls le commercial associé au contrat ou les membres du département gestion peuvent le modifier.[/red]"
                except Exception as e:
                    error_message += f"[red]Erreur lors de la vérification: {str(e)}[/red]"
                finally:
                    if "db_local" in locals():
                        db_local.close()

                console.print(Panel.fit(error_message, border_style="red"))

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

            # Affichage des informations dans un panneau élégant
            panel = Panel(
                contract_info,
                title=f"[bold yellow]Contrat #{contract.id}[/bold yellow]",
                border_style="yellow",
            )
            console.print(panel)

        except Exception as e:
            console.print(f"[bold red]Erreur lors de l'affichage du contrat:[/bold red] {str(e)}")
