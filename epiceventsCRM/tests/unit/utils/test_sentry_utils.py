import os
import pytest
from unittest.mock import patch, MagicMock

from epiceventsCRM.utils.sentry_utils import capture_exception, set_user_context, capture_message


class TestException(Exception):
    """Exception pour les tests."""

    pass


@pytest.fixture
def mock_env_sentry_dsn(monkeypatch):
    """Configure la variable d'environnement SENTRY_DSN."""
    monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.example.com/1")
    return "https://test@sentry.example.com/1"


@pytest.fixture
def mock_env_no_sentry_dsn(monkeypatch):
    """Supprime la variable d'environnement SENTRY_DSN."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)


def test_capture_exception_with_sentry_dsn(mock_env_sentry_dsn):
    """Test que les exceptions sont capturées quand SENTRY_DSN est configuré."""

    with patch("sentry_sdk.capture_exception") as mock_capture:
        # Fonction qui va lever une exception
        @capture_exception
        def func_with_error():
            raise TestException("Test d'erreur")

        # L'exception devrait être relancée
        with pytest.raises(TestException):
            func_with_error()

        # Vérifier que sentry_sdk.capture_exception a été appelé
        mock_capture.assert_called_once()


def test_capture_exception_without_sentry_dsn(mock_env_no_sentry_dsn):
    """Test que les exceptions sont capturées même quand SENTRY_DSN n'est pas configuré."""

    with patch("sentry_sdk.capture_exception") as mock_capture:
        # Fonction qui va lever une exception
        @capture_exception
        def func_with_error():
            raise TestException("Test d'erreur")

        # L'exception devrait être relancée
        with pytest.raises(TestException):
            func_with_error()

        # Vérifier que sentry_sdk.capture_exception a été appelé
        mock_capture.assert_called_once()


def test_capture_exception_no_exception():
    """Test que la fonction décorée retourne normalement quand il n'y a pas d'exception."""

    @capture_exception
    def func_without_error():
        return "success"

    assert func_without_error() == "success"


def test_set_user_context_with_sentry_dsn(mock_env_sentry_dsn):
    """Test que le contexte utilisateur est défini quand SENTRY_DSN est configuré."""

    with patch("sentry_sdk.set_user") as mock_set_user:
        user_id = 123
        email = "test@example.com"
        username = "testuser"

        set_user_context(user_id, email, username)

        # Vérifier que sentry_sdk.set_user a été appelé avec les bons arguments
        mock_set_user.assert_called_once_with({"id": user_id, "email": email, "username": username})


def test_set_user_context_without_sentry_dsn(mock_env_no_sentry_dsn):
    """Test que le contexte utilisateur est défini même quand SENTRY_DSN n'est pas configuré."""

    with patch("sentry_sdk.set_user") as mock_set_user:
        user_id = 123
        email = "test@example.com"
        username = "testuser"

        set_user_context(user_id, email, username)

        # Vérifier que sentry_sdk.set_user a été appelé avec les bons arguments
        mock_set_user.assert_called_once_with({"id": user_id, "email": email, "username": username})


def test_capture_message_with_sentry_dsn(mock_env_sentry_dsn):
    """Test que les messages sont capturés quand SENTRY_DSN est configuré."""

    with (
        patch("sentry_sdk.capture_message") as mock_capture_message,
        patch("sentry_sdk.push_scope") as mock_push_scope,
    ):

        # Configurer un contexte de scope mock
        scope_mock = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = scope_mock

        message = "Test message"
        level = "warning"
        extra = {"key1": "value1", "key2": "value2"}

        capture_message(message, level, extra)

        # Vérifier que le scope est configuré
        for key, value in extra.items():
            scope_mock.set_extra.assert_any_call(key, value)

        # Vérifier que le message est capturé
        mock_capture_message.assert_called_once_with(message, level=level)


def test_capture_message_without_extra(mock_env_sentry_dsn):
    """Test que les messages sont capturés sans extra quand SENTRY_DSN est configuré."""

    with (
        patch("sentry_sdk.capture_message") as mock_capture_message,
        patch("sentry_sdk.push_scope") as mock_push_scope,
    ):

        # Configurer un contexte de scope mock
        scope_mock = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = scope_mock

        message = "Test message"
        level = "info"

        capture_message(message, level)

        # Vérifier que set_extra n'a jamais été appelé
        scope_mock.set_extra.assert_not_called()

        # Vérifier que le message est capturé
        mock_capture_message.assert_called_once_with(message, level=level)


def test_capture_message_without_sentry_dsn(mock_env_no_sentry_dsn):
    """Test que les messages sont capturés même quand SENTRY_DSN n'est pas configuré."""

    with (
        patch("sentry_sdk.capture_message") as mock_capture_message,
        patch("sentry_sdk.push_scope") as mock_push_scope,
    ):
        # Configurer un contexte de scope mock
        scope_mock = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = scope_mock

        message = "Test message"
        level = "info"
        extra = {"key": "value"}

        capture_message(message, level, extra)

        # Vérifier que push_scope a été appelé
        mock_push_scope.assert_called_once()

        # Vérifier que set_extra a été appelé avec les bons arguments
        scope_mock.set_extra.assert_called_once_with("key", "value")

        # Vérifier que capture_message a été appelé
        mock_capture_message.assert_called_once_with(message, level=level)
