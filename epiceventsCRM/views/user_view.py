import click
from typing import List, Optional, Dict, Any
import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from epiceventsCRM.controllers.user_controller import UserController
from epiceventsCRM.views.base_view import BaseView, console
from epiceventsCRM.models.models import User
from sqlalchemy.orm import Session

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
        Enregistre les commandes de gestion des utilisateurs.
        
        Args:
            cli (click.Group): Le groupe de commandes CLI
            get_session: La fonction pour obtenir une session de base de données
            get_token: La fonction pour obtenir un token JWT
        """
        @cli.group()
        def user():
            """Commandes de gestion des utilisateurs."""
            pass
        
        user_view = UserView()
        
        # Commande de listage des utilisateurs
        @user.command("list-users")
        @click.option("--page", type=int, default=1, help="Numéro de page")
        @click.option("--page-size", type=int, default=10, help="Nombre d'utilisateurs par page")
        @click.pass_context
        def list_users(ctx, page, page_size):
            """Liste tous les utilisateurs."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit(
                    "[bold red]Veuillez vous connecter d'abord.[/bold red]",
                    border_style="red"
                ))
                return
                
            skip = (page - 1) * page_size
            users = user_view.controller.get_all(token, db, skip=skip, limit=page_size)
            
            if users:
                user_view.display_items(users)
                console.print(f"Page {page}, affichage de {len(users)} utilisateur(s)")
            else:
                console.print(Panel.fit(
                    "[bold yellow]Aucun utilisateur trouvé ou vous n'avez pas les permissions nécessaires.[/bold yellow]",
                    border_style="yellow"
                ))
        
        # Commande de création d'utilisateur
        @user.command("create")
        @click.option("--email", "-e", required=True, help="Email de l'utilisateur")
        @click.option("--password", "-p", required=True, help="Mot de passe de l'utilisateur")
        @click.option("--fullname", "-f", required=True, help="Nom complet de l'utilisateur")
        @click.option("--department", "-d", required=True, type=int, help="ID du département (1=commercial, 2=support, 3=gestion)")
        @click.pass_context
        def create_user(ctx, email, password, fullname, department):
            """Crée un nouvel utilisateur."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit(
                    "[bold red]Veuillez vous connecter d'abord.[/bold red]",
                    border_style="red"
                ))
                return
            
            user_data = {
                "email": email,
                "password": password,
                "fullname": fullname
            }
            
            user = user_view.controller.create_with_department(token, db, user_data, department)
            
            if user:
                console.print(Panel.fit(
                    f"[bold green]Utilisateur {user.id} créé avec succès.[/bold green]",
                    border_style="green"
                ))
                user_view.display_item(user)
            else:
                console.print(Panel.fit(
                    "[bold red]Échec de la création de l'utilisateur. Vérifiez vos permissions.[/bold red]",
                    border_style="red"
                ))
        
        # Commande pour obtenir un utilisateur spécifique
        @user.command("get")
        @click.argument("id", type=int)
        @click.pass_context
        def get_user(ctx, id):
            """Affiche les détails d'un utilisateur."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit(
                    "[bold red]Veuillez vous connecter d'abord.[/bold red]",
                    border_style="red"
                ))
                return
                
            user = user_view.controller.get(token, db, id)
            
            if user:
                user_view.display_item(user)
            else:
                console.print(Panel.fit(
                    f"[bold red]Utilisateur {id} non trouvé ou vous n'avez pas les permissions nécessaires.[/bold red]",
                    border_style="red"
                ))
        
        # Commande de mise à jour d'utilisateur
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
                console.print(Panel.fit(
                    "[bold red]Veuillez vous connecter d'abord.[/bold red]",
                    border_style="red"
                ))
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
                console.print(Panel.fit(
                    "[bold yellow]Aucune donnée à mettre à jour.[/bold yellow]",
                    border_style="yellow"
                ))
                return
            
            user = user_view.controller.update(token, db, id, user_data)
            
            if user:
                console.print(Panel.fit(
                    f"[bold green]Utilisateur {id} mis à jour avec succès.[/bold green]",
                    border_style="green"
                ))
                user_view.display_item(user)
            else:
                console.print(Panel.fit(
                    f"[bold red]Échec de la mise à jour de l'utilisateur {id}. Vérifiez l'ID et vos permissions.[/bold red]",
                    border_style="red"
                ))
        
        # Commande de suppression d'utilisateur
        @user.command("delete")
        @click.argument("id", type=int)
        @click.option("--confirm", is_flag=True, help="Confirmer la suppression sans demander")
        @click.pass_context
        def delete_user(ctx, id, confirm):
            """Supprime un utilisateur."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit(
                    "[bold red]Veuillez vous connecter d'abord.[/bold red]",
                    border_style="red"
                ))
                return
            
            # Vérifier si l'utilisateur existe
            user = user_view.controller.get(token, db, id)
            if not user:
                console.print(Panel.fit(
                    f"[bold red]Utilisateur {id} non trouvé ou vous n'avez pas les permissions nécessaires.[/bold red]",
                    border_style="red"
                ))
                return
            
            # Confirmation de suppression
            if not confirm:
                should_delete = Confirm.ask(f"Êtes-vous sûr de vouloir supprimer l'utilisateur {id} ({user.fullname}) ?")
                if not should_delete:
                    console.print(Panel.fit(
                        "[bold yellow]Suppression annulée.[/bold yellow]",
                        border_style="yellow"
                    ))
                    return
            
            # Suppression
            if user_view.controller.delete(token, db, id):
                console.print(Panel.fit(
                    f"[bold green]Utilisateur {id} supprimé avec succès.[/bold green]",
                    border_style="green"
                ))
            else:
                console.print(Panel.fit(
                    f"[bold red]Échec de la suppression de l'utilisateur {id}.[/bold red]",
                    border_style="red"
                ))
        
        # Commande pour trouver un utilisateur par email
        @user.command("find")
        @click.option("--email", "-e", required=True, help="Email de l'utilisateur à rechercher")
        @click.pass_context
        def find_user(ctx, email):
            """Recherche un utilisateur par son email."""
            db = get_session()
            token = get_token()
            
            if not token:
                console.print(Panel.fit(
                    "[bold red]Veuillez vous connecter d'abord.[/bold red]",
                    border_style="red"
                ))
                return
                
            user = user_view.controller.get_by_email(token, db, email)
            
            if user:
                user_view.display_item(user)
            else:
                console.print(Panel.fit(
                    f"[bold red]Aucun utilisateur trouvé avec l'email {email} ou vous n'avez pas les permissions nécessaires.[/bold red]",
                    border_style="red"
                ))
    
    def display_items(self, users: List[Any]):
        """
        Affiche une liste d'utilisateurs sous forme de tableau.
        
        Args:
            users (List[Any]): La liste d'utilisateurs à afficher
        """
        table = Table(title="Liste des utilisateurs")
        
        # Définition des colonnes
        table.add_column("ID", style="cyan")
        table.add_column("Email", style="green")
        table.add_column("Nom complet", style="magenta")
        table.add_column("Département", style="yellow")
        
        # Ajout des lignes
        for user in users:
            department_name = user.department.departement_name if user.department else "N/A"
            table.add_row(
                str(user.id),
                user.email,
                user.fullname,
                department_name
            )
        
        console.print(table)
    
    def display_item(self, user: User) -> None:
        """
        Affiche les détails d'un utilisateur.
        
        Args:
            user (User): L'utilisateur à afficher
        """
        table = Table(title=f"Détails de l'utilisateur #{user.id}")
        
        # Définition des colonnes
        table.add_column("Propriété", style="cyan")
        table.add_column("Valeur", style="green")
        
        # Ajout des informations
        department_name = user.department.departement_name if user.department else "N/A"
        
        table.add_row("ID", str(user.id))
        table.add_row("Email", user.email)
        table.add_row("Nom complet", user.fullname)
        table.add_row("Département", department_name)
        
        console.print(table) 