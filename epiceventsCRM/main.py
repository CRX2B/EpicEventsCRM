import click
from epiceventsCRM.views.auth_view import auth
from epiceventsCRM.views.user_management_view import UserManagementView
from epiceventsCRM.views.client_view import ClientView
from epiceventsCRM.views.contract_view import ContractView
from epiceventsCRM.views.event_view import EventView
from epiceventsCRM.database import get_session
from epiceventsCRM.utils.token_manager import get_token
from epiceventsCRM.init_db import init_db

@click.group()
def cli():
    """Epic Events CRM - Gestion des événements"""
    pass

# Ajout des commandes d'authentification
cli.add_command(auth)

# Ajout de la commande d'initialisation de la base de données
cli.add_command(init_db)

# Enregistrement des commandes de gestion des utilisateurs
UserManagementView.register_commands(cli, get_session, get_token)

# Enregistrement des commandes de gestion des clients
ClientView.register_commands(cli, get_session, get_token)

# Enregistrement des commandes de gestion des contrats
ContractView.register_commands(cli, get_session, get_token)

# Enregistrement des commandes de gestion des événements
EventView.register_commands(cli, get_session, get_token)

if __name__ == "__main__":
    cli()
