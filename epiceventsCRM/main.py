import click
from epiceventsCRM.views.auth_view import auth

@click.group()
def cli():
    """Epic Events CRM - Gestion des événements"""
    pass

# Ajout des commandes d'authentification
cli.add_command(auth)

if __name__ == "__main__":
    cli()
