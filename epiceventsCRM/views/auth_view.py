import click
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from typing import Optional, Dict
from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.database import get_db
from sqlalchemy.orm import Session

console = Console()

class AuthView:
    """
    Vue pour la gestion de l'authentification.
    """
    
    def __init__(self, auth_controller: AuthController):
        self.auth_controller = auth_controller
    
    def login(self, db: Session) -> Optional[Dict]:
        """
        Affiche l'interface de connexion et gère l'authentification.
        
        Args:
            db (Session): La session de base de données
            
        Returns:
            Optional[Dict]: Les informations de l'utilisateur si authentifié, None sinon
        """
        console.print(Panel.fit(
            "[bold blue]Connexion à Epic Events CRM[/bold blue]",
            border_style="blue"
        ))
        
        email = Prompt.ask("Email")
        password = Prompt.ask("Mot de passe", password=True)
        
        result = self.auth_controller.login(db, email, password)
        
        if result:
            console.print(Panel.fit(
                "[bold green]Connexion réussie ![/bold green]\n"
                f"Bienvenue {result['user']['fullname']}",
                border_style="green"
            ))
            return result
        else:
            console.print(Panel.fit(
                "[bold red]Échec de la connexion[/bold red]\n"
                "Email ou mot de passe incorrect",
                border_style="red"
            ))
            return None
    
    def logout(self):
        """
        Affiche un message de déconnexion.
        """
        console.print(Panel.fit(
            "[bold blue]Déconnexion[/bold blue]\n"
            "Au revoir !",
            border_style="blue"
        ))

# Création des instances globales
auth_controller = AuthController()
auth_view = AuthView(auth_controller)

@click.group()
def auth():
    """Commandes d'authentification"""
    pass

@auth.command()
def login():
    """Se connecter à l'application"""
    db = next(get_db())
    auth_view.login(db)

@auth.command()
def logout():
    """Se déconnecter de l'application"""
    auth_view.logout() 