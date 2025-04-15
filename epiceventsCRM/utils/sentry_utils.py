"""Utilitaires pour l'intégration de Sentry dans l'application."""

import os
from functools import wraps
import sentry_sdk

def get_sentry_dsn():
    """
    Récupère le DSN Sentry de manière dynamique.
    Cela permet de s'assurer que nous avons toujours la dernière valeur.
    """
    return os.getenv("SENTRY_DSN")

def capture_exception(func):
    """
    Décorateur pour capturer les exceptions et les envoyer à Sentry.

    Args:
        func (Callable): La fonction à décorer

    Returns:
        Callable: La fonction décorée

    Raises:
        Exception: L'exception originale est relancée après capture
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Capture l'exception dans Sentry
            sentry_sdk.capture_exception(e)
            # Relève l'exception pour ne pas masquer l'erreur
            raise

    return wrapper


def set_user_context(user_id=None, email=None, username=None):
    """
    Définit le contexte utilisateur pour Sentry.

    Args:
        user_id (str, optional): L'ID de l'utilisateur
        email (str, optional): L'email de l'utilisateur
        username (str, optional): Le nom d'utilisateur
    """
    sentry_sdk.set_user({"id": user_id, "email": email, "username": username})


def capture_message(message, level="info", extra=None):
    """
    Envoie un message à Sentry avec un niveau de sévérité spécifié.

    Args:
        message (str): Le message à envoyer
        level (str, optional): Le niveau de sévérité (info, warning, error, etc.)
        extra (dict, optional): Informations supplémentaires à inclure
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)
        # Forcer l'envoi immédiat
        sentry_sdk.flush()
