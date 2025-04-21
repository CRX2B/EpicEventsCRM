import os
import pytest
import sentry_sdk
from unittest.mock import patch, MagicMock

from epiceventsCRM.utils.sentry_utils import (
    capture_exception,
    set_user_context,
    capture_message,
)


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


@patch("sentry_sdk.capture_exception")
def test_capture_exception_decorator(mock_sentry_capture):
    """Teste que le décorateur capture_exception appelle sentry_sdk et relève l'exception."""

    @capture_exception
    def function_that_raises():
        raise ValueError("Test error")

    with pytest.raises(ValueError) as excinfo:
        function_that_raises()

    assert "Test error" in str(excinfo.value)
    mock_sentry_capture.assert_called_once()
    # Vérifier que l'exception passée à Sentry est bien celle levée
    call_args, _ = mock_sentry_capture.call_args
    assert isinstance(call_args[0], ValueError)
    assert str(call_args[0]) == "Test error"


@patch("sentry_sdk.set_user")
def test_set_user_context(mock_sentry_set_user):
    """Teste que set_user_context appelle sentry_sdk.set_user avec les bonnes données."""
    user_info = {"user_id": "user123", "email": "user@example.com", "username": "testuser"}
    set_user_context(**user_info)
    mock_sentry_set_user.assert_called_once_with(
        {"id": "user123", "email": "user@example.com", "username": "testuser"}
    )


@patch("sentry_sdk.capture_message")
@patch("sentry_sdk.flush")
@patch("sentry_sdk.push_scope")
def test_capture_message_simple(mock_push_scope, mock_flush, mock_sentry_capture):
    """Teste l'envoi d'un message simple à Sentry."""
    mock_scope = MagicMock()
    mock_push_scope.return_value.__enter__.return_value = mock_scope

    message = "Test message"
    level = "warning"

    capture_message(message, level=level)

    mock_sentry_capture.assert_called_once_with(message, level=level)
    mock_scope.set_extra.assert_not_called()
    mock_flush.assert_called_once()


@patch("sentry_sdk.capture_message")
@patch("sentry_sdk.flush")
@patch("sentry_sdk.push_scope")
def test_capture_message_with_extra(mock_push_scope, mock_flush, mock_sentry_capture):
    """Teste l'envoi d'un message à Sentry avec des données supplémentaires."""
    mock_scope = MagicMock()
    mock_push_scope.return_value.__enter__.return_value = mock_scope

    message = "Another test message"
    level = "error"
    extra_data = {"request_id": "abc-123", "details": "More info"}

    capture_message(message, level=level, extra=extra_data)

    mock_sentry_capture.assert_called_once_with(message, level=level)
    mock_scope.set_extra.assert_any_call("request_id", "abc-123")
    mock_scope.set_extra.assert_any_call("details", "More info")
    assert mock_scope.set_extra.call_count == 2
    mock_flush.assert_called_once()


def test_capture_exception_with_sentry_dsn(mock_env_sentry_dsn):
    """Test que les exceptions sont capturées quand SENTRY_DSN est configuré."""

    with patch("sentry_sdk.capture_exception") as mock_capture:

        @capture_exception
        def func_with_error():
            raise TestException("Test d'erreur")

        with pytest.raises(TestException):
            func_with_error()

        mock_capture.assert_called_once()


def test_capture_exception_without_sentry_dsn(mock_env_no_sentry_dsn):
    """Test que les exceptions sont capturées même quand SENTRY_DSN n'est pas configuré."""

    with patch("sentry_sdk.capture_exception") as mock_capture:

        @capture_exception
        def func_with_error():
            raise TestException("Test d'erreur")

        with pytest.raises(TestException):
            func_with_error()

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

        mock_set_user.assert_called_once_with({"id": user_id, "email": email, "username": username})


def test_set_user_context_without_sentry_dsn(mock_env_no_sentry_dsn):
    """Test que le contexte utilisateur est défini même quand SENTRY_DSN n'est pas configuré."""

    with patch("sentry_sdk.set_user") as mock_set_user:
        user_id = 123
        email = "test@example.com"
        username = "testuser"

        set_user_context(user_id, email, username)

        mock_set_user.assert_called_once_with({"id": user_id, "email": email, "username": username})


def test_capture_message_with_sentry_dsn(mock_env_sentry_dsn):
    """Test que les messages sont capturés quand SENTRY_DSN est configuré."""

    with (
        patch("sentry_sdk.capture_message") as mock_capture_message,
        patch("sentry_sdk.push_scope") as mock_push_scope,
    ):

        scope_mock = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = scope_mock

        message = "Test message"
        level = "warning"
        extra = {"key1": "value1", "key2": "value2"}

        capture_message(message, level, extra)

        for key, value in extra.items():
            scope_mock.set_extra.assert_any_call(key, value)

        mock_capture_message.assert_called_once_with(message, level=level)


def test_capture_message_without_extra(mock_env_sentry_dsn):
    """Test que les messages sont capturés sans extra quand SENTRY_DSN est configuré."""

    with (
        patch("sentry_sdk.capture_message") as mock_capture_message,
        patch("sentry_sdk.push_scope") as mock_push_scope,
    ):

        scope_mock = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = scope_mock

        message = "Test message"
        level = "info"

        capture_message(message, level)

        scope_mock.set_extra.assert_not_called()

        mock_capture_message.assert_called_once_with(message, level=level)


def test_capture_message_without_sentry_dsn(mock_env_no_sentry_dsn):
    """Test que les messages sont capturés même quand SENTRY_DSN n'est pas configuré."""

    with (
        patch("sentry_sdk.capture_message") as mock_capture_message,
        patch("sentry_sdk.push_scope") as mock_push_scope,
    ):

        scope_mock = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = scope_mock

        message = "Test message"
        level = "info"
        extra = {"key": "value"}

        capture_message(message, level, extra)

        mock_push_scope.assert_called_once()

        scope_mock.set_extra.assert_called_once_with("key", "value")

        mock_capture_message.assert_called_once_with(message, level=level)
