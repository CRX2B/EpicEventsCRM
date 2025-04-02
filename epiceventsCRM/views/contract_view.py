import click
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.controllers.client_controller import ClientController


class ContractView:
    """
    Vue pour gérer les contrats via l'interface en ligne de commande
    """
    
    def __init__(self, session: Session, token: str):
        """
        Initialise la vue avec une session et un token
        
        Args:
            session: Session SQLAlchemy active
            token: Token JWT pour l'authentification
        """
        self.session = session
        self.token = token
        self.contract_controller = ContractController(session)
        self.client_controller = ClientController(session)
    
    def display_contract(self, contract: Dict) -> None:
        """
        Affiche les détails d'un contrat
        
        Args:
            contract: Dictionnaire représentant un contrat
        """
        click.echo("-" * 50)
        click.echo(f"ID: {contract.id}")
        click.echo(f"Client ID: {contract.client_id}")
        click.echo(f"Montant total: {contract.amount} €")
        click.echo(f"Montant restant: {contract.remaining_amount} €")
        click.echo(f"Date de création: {contract.create_date}")
        click.echo(f"Statut: {'Signé' if contract.status else 'Non signé'}")
        click.echo(f"Commercial ID: {contract.sales_contact_id}")
        click.echo("-" * 50)
    
    def list_contracts(self) -> None:
        """
        Affiche la liste des contrats accessibles par l'utilisateur
        """
        success, result = self.contract_controller.list_contracts(self.token)
        
        if not success:
            click.echo(f"Erreur: {result}")
            return
            
        if not result:
            click.echo("Aucun contrat trouvé.")
            return
            
        click.echo(f"Liste des contrats ({len(result)} trouvés):")
        for contract in result:
            self.display_contract(contract)
    
    def get_contract_by_id(self, contract_id: int) -> None:
        """
        Affiche les détails d'un contrat spécifique
        
        Args:
            contract_id: ID du contrat à afficher
        """
        success, result = self.contract_controller.get_contract(self.token, contract_id)
        
        if not success:
            click.echo(f"Erreur: {result}")
            return
            
        click.echo("Détails du contrat:")
        self.display_contract(result)
    
    def create_contract(self) -> None:
        """
        Interface pour créer un nouveau contrat
        """
        # Afficher la liste des clients pour sélection
        success, clients = self.client_controller.list_clients(self.token)
        
        if not success:
            click.echo(f"Erreur: {clients}")
            return
            
        if not clients:
            click.echo("Aucun client trouvé. Veuillez d'abord créer un client.")
            return
            
        click.echo("Liste des clients disponibles:")
        for i, client in enumerate(clients, 1):
            click.echo(f"{i}. {client.fullname} (ID: {client.id}) - {client.enterprise}")
        
        # Demander à l'utilisateur de sélectionner un client
        client_index = click.prompt("Sélectionnez un client (numéro)", type=int) - 1
        
        if client_index < 0 or client_index >= len(clients):
            click.echo("Sélection invalide.")
            return
            
        client_id = clients[client_index].id
        
        # Demander le montant du contrat
        amount = click.prompt("Montant du contrat (€)", type=float)
        
        # Demander si un commercial spécifique doit être assigné
        assign_specific = click.confirm("Voulez-vous assigner un commercial spécifique?", default=False)
        
        sales_contact_id = None
        if assign_specific:
            sales_contact_id = click.prompt("ID du commercial", type=int)
        
        # Créer le contrat
        success, result = self.contract_controller.create_contract(
            token=self.token,
            client_id=client_id,
            amount=amount,
            sales_contact_id=sales_contact_id
        )
        
        if not success:
            click.echo(f"Erreur: {result}")
            return
            
        click.echo("Contrat créé avec succès:")
        self.display_contract(result)
    
    def update_contract(self, contract_id: int) -> None:
        """
        Interface pour mettre à jour un contrat existant
        
        Args:
            contract_id: ID du contrat à mettre à jour
        """
        # Vérifier si le contrat existe et si l'utilisateur y a accès
        success, contract = self.contract_controller.get_contract(self.token, contract_id)
        
        if not success:
            click.echo(f"Erreur: {contract}")
            return
            
        click.echo("Contrat actuel:")
        self.display_contract(contract)
        
        # Demander quels champs mettre à jour
        data = {}
        
        if click.confirm("Mettre à jour le montant?", default=False):
            data["amount"] = click.prompt("Nouveau montant (€)", type=float)
            
        if click.confirm("Mettre à jour le montant restant?", default=False):
            data["remaining_amount"] = click.prompt("Nouveau montant restant (€)", type=float)
            
        if click.confirm("Mettre à jour le statut?", default=False):
            data["status"] = click.confirm("Contrat signé?", default=contract.status)
            
        if not data:
            click.echo("Aucune modification demandée.")
            return
            
        # Mettre à jour le contrat
        success, result = self.contract_controller.update_contract(self.token, contract_id, data)
        
        if not success:
            click.echo(f"Erreur: {result}")
            return
            
        click.echo("Contrat mis à jour avec succès:")
        self.display_contract(result)
    
    def delete_contract(self, contract_id: int) -> None:
        """
        Interface pour supprimer un contrat
        
        Args:
            contract_id: ID du contrat à supprimer
        """
        # Confirmer la suppression
        if not click.confirm(f"Êtes-vous sûr de vouloir supprimer le contrat {contract_id}?", default=False):
            click.echo("Suppression annulée.")
            return
            
        # Supprimer le contrat
        success, message = self.contract_controller.delete_contract(self.token, contract_id)
        
        if not success:
            click.echo(f"Erreur: {message}")
            return
            
        click.echo(message)
    
    @staticmethod
    def register_commands(cli_group, get_session, get_token):
        """
        Enregistre les commandes CLI pour la gestion des contrats
        
        Args:
            cli_group: Groupe de commandes Click
            get_session: Fonction pour obtenir une session DB
            get_token: Fonction pour obtenir le token JWT
        """
        
        @cli_group.group()
        def contract():
            """Gestion des contrats"""
            pass
        
        @contract.command("list")
        def list_contracts():
            """Liste tous les contrats accessibles"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour accéder aux contrats.")
                return
            contract_view = ContractView(session, token)
            contract_view.list_contracts()
        
        @contract.command("get")
        @click.argument("contract_id", type=int)
        def get_contract(contract_id):
            """Affiche les détails d'un contrat spécifique"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour accéder aux contrats.")
                return
            contract_view = ContractView(session, token)
            contract_view.get_contract_by_id(contract_id)
        
        @contract.command("create")
        def create_contract():
            """Crée un nouveau contrat"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour créer un contrat.")
                return
            contract_view = ContractView(session, token)
            contract_view.create_contract()
        
        @contract.command("update")
        @click.argument("contract_id", type=int)
        def update_contract(contract_id):
            """Met à jour un contrat existant"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour mettre à jour un contrat.")
                return
            contract_view = ContractView(session, token)
            contract_view.update_contract(contract_id)
        
        @contract.command("delete")
        @click.argument("contract_id", type=int)
        def delete_contract(contract_id):
            """Supprime un contrat existant"""
            session = get_session()
            token = get_token()
            if not token:
                click.echo("Erreur: Vous devez être connecté pour supprimer un contrat.")
                return
            contract_view = ContractView(session, token)
            contract_view.delete_contract(contract_id) 