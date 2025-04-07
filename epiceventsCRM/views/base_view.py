import click
from typing import Callable, Any, Dict, List, Optional
from sqlalchemy.orm import Session
from rich.console import Console
from rich.panel import Panel
from epiceventsCRM.controllers.base_controller import BaseController

# Création d'une console Rich pour l'affichage
console = Console()

class BaseView:
    """
    Vue de base qui fournit des fonctionnalités CLI génériques.
    """
    
    def __init__(self, controller: BaseController, entity_name: str, entity_name_plural: str = None):
        """
        Initialise la vue avec un contrôleur et un nom d'entité.
        
        Args:
            controller (BaseController): Le contrôleur à utiliser
            entity_name (str): Le nom de l'entité (au singulier, pour les messages)
            entity_name_plural (str, optional): Le nom de l'entité au pluriel (pour les messages)
        """
        self.controller = controller
        self.entity_name = entity_name
        self.entity_name_plural = entity_name_plural or f"{entity_name}s"
    
    @staticmethod
    def register_commands(cli: click.Group, get_session: Callable, get_token: Callable):
        """
        Pour être implémenté par les classes enfants.
        Enregistre les commandes CLI.
        
        Args:
            cli (click.Group): Le groupe de commandes CLI
            get_session (Callable): La fonction pour obtenir une session de base de données
            get_token (Callable): La fonction pour obtenir un token JWT
        """
        raise NotImplementedError("Les vues enfants doivent implémenter register_commands")
    
    def create_list_command(self) -> Callable:
        """
        Crée une commande pour lister toutes les entités.
        
        Returns:
            Callable: La fonction de commande
        """
        @click.command(f"list-{self.entity_name_plural}")
        @click.option("--skip", "-s", default=0, help="Nombre d'éléments à sauter")
        @click.option("--limit", "-l", default=100, help="Nombre maximum d'éléments à afficher")
        @click.pass_context
        def list_items(ctx, skip, limit):
            """Liste tous les éléments."""
            db: Session = ctx.obj["session"]
            token = ctx.obj["token"]
            items = self.controller.get_all(token, db, skip, limit)
            
            if not items:
                console.print(Panel.fit(
                    f"[bold yellow]Aucun {self.entity_name_plural} trouvé.[/bold yellow]",
                    border_style="yellow"
                ))
                return
                
            self.display_items(items)
        
        return list_items
    
    def create_get_command(self) -> Callable:
        """
        Crée une commande pour obtenir une entité par son ID.
        
        Returns:
            Callable: La fonction de commande
        """
        @click.command(f"get-{self.entity_name}")
        @click.argument("id", type=int)
        @click.pass_context
        def get_item(ctx, id):
            """Obtient un élément par son ID."""
            db: Session = ctx.obj["session"]
            token = ctx.obj["token"]
            item = self.controller.get(token, db, id)
            
            if not item:
                console.print(Panel.fit(
                    f"[bold red]{self.entity_name.capitalize()} {id} non trouvé.[/bold red]",
                    border_style="red"
                ))
                return
                
            self.display_item(item)
        
        return get_item
    
    def create_delete_command(self) -> Callable:
        """
        Crée une commande pour supprimer une entité.
        
        Returns:
            Callable: La fonction de commande
        """
        @click.command(f"delete-{self.entity_name}")
        @click.argument("id", type=int)
        @click.confirmation_option(prompt=f"Êtes-vous sûr de vouloir supprimer ce {self.entity_name} ?")
        @click.pass_context
        def delete_item(ctx, id):
            """Supprime un élément par son ID."""
            db: Session = ctx.obj["session"]
            token = ctx.obj["token"]
            
            if not token:
                console.print(Panel.fit(
                    f"[bold red]Vous devez être connecté pour supprimer un {self.entity_name}.[/bold red]",
                    border_style="red"
                ))
                return
            
            # Vérifier si l'entité existe avant de tenter de la supprimer
            item = self.controller.get(token, db, id)
            if not item:
                console.print(Panel.fit(
                    f"[bold red]Le {self.entity_name} {id} n'existe pas ou vous n'avez pas les permissions pour y accéder.[/bold red]",
                    border_style="red"
                ))
                return
            
            # Tenter la suppression
            success = self.controller.delete(token, db, id)
            
            if success:
                console.print(Panel.fit(
                    f"[bold green]{self.entity_name.capitalize()} {id} supprimé avec succès.[/bold green]",
                    border_style="green"
                ))
            else:
                # Message d'erreur plus détaillé
                console.print(Panel.fit(
                    f"[bold red]Échec de la suppression du {self.entity_name} {id}.[/bold red]\n"
                    f"[red]Cette action peut être restreinte pour les raisons suivantes:[/red]\n"
                    f"[red]• Vous n'avez pas les permissions requises (département gestion uniquement)[/red]\n"
                    f"[red]• L'élément est référencé par d'autres données dans le système[/red]",
                    border_style="red"
                ))
        
        return delete_item
    
    def display_items(self, items: List[Any]):
        """
        Affiche une liste d'éléments.
        À implémenter par les classes enfants.
        
        Args:
            items (List[Any]): La liste d'éléments à afficher
        """
        raise NotImplementedError("Les vues enfants doivent implémenter display_items")
    
    def display_item(self, item: Any):
        """
        Affiche un élément.
        À implémenter par les classes enfants.
        
        Args:
            item (Any): L'élément à afficher
        """
        raise NotImplementedError("Les vues enfants doivent implémenter display_item") 