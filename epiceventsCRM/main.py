import os
import sys
import traceback

import click
import sentry_sdk
from dotenv import load_dotenv

from epiceventsCRM.database import get_session
from epiceventsCRM.init_db import init_db
from epiceventsCRM.utils.token_manager import get_token
from epiceventsCRM.views.auth_view import auth
from epiceventsCRM.views.client_view import ClientView
from epiceventsCRM.views.contract_view import ContractView
from epiceventsCRM.views.event_view import EventView
from epiceventsCRM.views.user_view import UserView

# Initialisation de Sentry
load_dotenv()
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Envoi des données utilisateur comme les en-têtes de requête et l'IP
        send_default_pii=True,
        # Performance de suivi des transactions
        traces_sample_rate=1.0,
        # Suivi des profils des performances
        profiles_sample_rate=1.0,
        # Activer les messages de transport dans la console
        debug=True,
        shutdown_timeout=2.0,
    )


@click.group()
@click.pass_context
def cli(ctx):
    """Epic Events CRM - Gestion des événements"""
    # Initialiser le contexte
    ctx.ensure_object(dict)
    # Fournir la session, le token et les fonctions d'accès au contexte
    ctx.obj["session"] = get_session()
    ctx.obj["token"] = get_token()
    ctx.obj["get_session"] = get_session
    ctx.obj["get_token"] = get_token


# Handler pour les exceptions non gérées
def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Handler global pour les exceptions non gérées.
    Capture l'exception dans Sentry et affiche un message d'erreur convivial.
    """
    # Ignorer les exceptions liées à KeyboardInterrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Capturer l'exception dans Sentry
    if SENTRY_DSN:
        sentry_sdk.capture_exception((exc_type, exc_value, exc_traceback))

    # Afficher un message d'erreur pour l'utilisateur
    print("Une erreur inattendue s'est produite.")
    print("Message d'erreur:", str(exc_value))

    # Afficher la trace complète en mode développement
    if os.getenv("EPIC_EVENTS_ENV") == "development":
        print("\nTraceback:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)


# Remplacer le handler d'exceptions par défaut
sys.excepthook = handle_exception

# Ajout des commandes d'authentification
cli.add_command(auth)
# Ajout de la commande d'initialisation de la base de données
cli.add_command(init_db)

# Enregistrement des commandes de gestion des utilisateurs
UserView.register_commands(cli, get_session, get_token)

# Enregistrement des commandes de gestion des clients
ClientView.register_commands(cli, get_session, get_token)

# Enregistrement des commandes de gestion des contrats
ContractView.register_commands(cli, get_session, get_token)

# Enregistrement des commandes de gestion des événements
EventView.register_commands(cli, get_session, get_token)

if __name__ == "__main__":
    cli()
