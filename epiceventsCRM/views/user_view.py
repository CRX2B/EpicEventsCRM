from typing import Any, List

import click
from rich.panel import Panel
from rich.table import Table

from epiceventsCRM.controllers.user_controller import UserController
from epiceventsCRM.models.models import User
from epiceventsCRM.utils.permissions import PermissionError
from epiceventsCRM.views.base_view import BaseView, console


class UserView(BaseView):
    """
    Vue unifiée pour la gestion des utilisateurs via CLI.
    """

    def __init__(self):
        """
        Initialise la vue utilisateur avec le contrôleur approprié.
        """
        super().__init__(UserController(), "user", "users")

    @staticmethod
    def register_commands(cli: click.Group, get_session, get_token):
        """
        Enregistre les commandes liées aux utilisateurs dans le CLI.

        Args:
            cli (click.Group): Le groupe de commandes CLI
            get_session: Fonction pour obtenir une session de base de données
            get_token: Fonction pour obtenir le token JWT
        """

        @cli.group("user")
        def user():
            """Commandes pour la gestion des utilisateurs."""
            pass

        user_view = UserView()

        user.add_command(user_view.create_list_command())
        user.add_command(user_view.create_get_command())
        user.add_command(user_view.create_delete_command())

        @user.command("create")
        @click.option("--email", "-e", required=True, help="Email de l'utilisateur")
        @click.option("--password", "-p", required=True, help="Mot de passe de l'utilisateur")
        @click.option("--fullname", "-f", required=True, help="Nom complet de l'utilisateur")
        @click.option(
            "--department",
            "-d",
            required=True,
            type=int,
            help="ID du département (1=commercial, 2=support, 3=gestion)",
        )
        @click.pass_context
        def create_user(ctx, email, password, fullname, department):
            """Crée un nouvel utilisateur."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]", border_style="red"
                    )
                )
                return

            user_data = {"email": email, "password": password, "fullname": fullname}

            try:
                user = user_view.controller.create_with_department(token, db, user_data, department)
                if user:
                    console.print(
                        Panel.fit(
                            f"[bold green]Utilisateur {user.id} créé avec succès.[/bold green]",
                            border_style="green",
                        )
                    )
                    user_view.display_item(user)
                else:
                    console.print(
                        Panel.fit(
                            "[bold red]Échec de la création de l'utilisateur.[/bold red]\\nVérifiez les informations fournies et vos permissions.",
                            title="Erreur de Création",
                            border_style="red",
                        )
                    )
            except PermissionError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\\n{e.message}",
                        title="Erreur d'Autorisation",
                        border_style="red",
                    )
                )
            except ValueError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur de données:[/bold red]\\n{str(e)}",
                        title="Erreur de Création",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la création :[/bold red]\\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
                    )
                )

        @user.command("update")
        @click.argument("id", type=int)
        @click.option("--email", "-e", help="Email de l'utilisateur")
        @click.option("--password", "-p", help="Mot de passe de l'utilisateur")
        @click.option("--fullname", "-f", help="Nom complet de l'utilisateur")
        @click.option("--department", "-d", type=int, help="ID du département")
        @click.pass_context
        def update_user(ctx, id, email, password, fullname, department):
            """Met à jour un utilisateur existant."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]", border_style="red"
                    )
                )
                return

            user_data = {}
            if email:
                user_data["email"] = email
            if password:
                user_data["password"] = password
            if fullname:
                user_data["fullname"] = fullname
            if department:
                user_data["departement_id"] = department

            if not user_data:
                console.print(
                    Panel.fit(
                        "[bold yellow]Aucune donnée à mettre à jour.[/bold yellow]",
                        border_style="yellow",
                    )
                )
                return

            try:
                user = user_view.controller.update(token, db, id, user_data)
                if user:
                    console.print(
                        Panel.fit(
                            f"[bold green]Utilisateur {id} mis à jour avec succès.[/bold green]",
                            border_style="green",
                        )
                    )
                    user_view.display_item(user)
                else:
                    console.print(
                        Panel.fit(
                            f"[bold red]Échec de la mise à jour de l'utilisateur {id}.[/bold red]\\nVérifiez l'ID et vos permissions.",
                            title="Erreur de Mise à Jour",
                            border_style="red",
                        )
                    )
            except PermissionError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\\n{e.message}",
                        title="Erreur d'Autorisation",
                        border_style="red",
                    )
                )
            except ValueError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur de données:[/bold red]\\n{str(e)}",
                        title="Erreur de Mise à Jour",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la mise à jour :[/bold red]\\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
                    )
                )

        @user.command("find")
        @click.option("--email", "-e", required=True, help="Email de l'utilisateur à rechercher")
        @click.pass_context
        def find_user(ctx, email):
            """Recherche un utilisateur par son email."""
            db = get_session()
            token = get_token()

            if not token:
                console.print(
                    Panel.fit(
                        "[bold red]Veuillez vous connecter d'abord.[/bold red]", border_style="red"
                    )
                )
                return

            try:
                user = user_view.controller.find_by_email(token, db, email)
                if user:
                    console.print(
                        Panel.fit(
                            "[bold green]Utilisateur trouvé.[/bold green]", border_style="green"
                        )
                    )
                    user_view.display_item(user)
                else:
                    console.print(
                        Panel.fit(
                            f"[bold yellow]Aucun utilisateur trouvé avec l'email: {email}[/bold yellow]",
                            border_style="yellow",
                        )
                    )
            except PermissionError as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Permission refusée:[/bold red]\\n{e.message}",
                        title="Erreur d'Autorisation",
                        border_style="red",
                    )
                )
            except Exception as e:
                console.print(
                    Panel.fit(
                        f"[bold red]Erreur lors de la recherche :[/bold red]\\n{str(e)}",
                        title="Erreur Inattendue",
                        border_style="red",
                    )
                )

    def display_items(self, users: List[Any]):
        """
        Affiche une liste d'utilisateurs sous forme de tableau.
        """
        if not users:
            console.print("[yellow]Aucun utilisateur à afficher.[/yellow]")
            return

        table = Table(
            title="[bold]Liste des utilisateurs[/bold]",
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
        )

        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Nom complet", style="green")
        table.add_column("Email", style="yellow")
        table.add_column("Département", style="blue")

        for user in users:
            department_name = user.department.departement_name if user.department else "Non défini"
            table.add_row(
                str(user.id),
                user.fullname,
                user.email,
                department_name,
            )

        console.print(table)

    def display_item(self, user: User) -> None:
        """
        Affiche les détails d'un utilisateur spécifique dans un Panel.
        """
        if not user:
            console.print("[red]Aucun utilisateur à afficher.[/red]")
            return

        table = Table(
            title=f"Détails de l'utilisateur #{user.id}",
            show_header=False,
            box=None,
            padding=(0, 1),
        )
        table.add_column(style="cyan")
        table.add_column(style="green")

        table.add_row("ID:", str(user.id))
        table.add_row("Nom complet:", user.fullname)
        table.add_row("Email:", user.email)
        # Ne pas afficher le mot de passe
        department_name = user.department.departement_name if user.department else "Non défini"
        table.add_row("Département:", department_name)

        console.print(Panel(table, title=f"Utilisateur {user.fullname}", border_style="blue"))
