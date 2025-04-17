import pytest
from unittest.mock import Mock, patch
from rich.console import Console
from rich.panel import Panel
from click.testing import CliRunner

from epiceventsCRM.views.auth_view import AuthView, auth_controller, auth_view, login, logout
from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.models.models import User


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def mock_auth_controller_instance():
    return Mock(spec=AuthController)


@pytest.fixture
def mock_auth_view(mock_auth_controller_instance):
    return AuthView(mock_auth_controller_instance)


class TestAuthView:
    """Tests unitaires pour AuthView."""

    @patch("rich.prompt.Prompt.ask")
    def test_login_success(
        self, mock_ask, mock_db, mock_auth_controller_instance, mock_auth_view, capsys
    ):
        """Teste une connexion réussie via AuthView."""
        mock_ask.side_effect = ["test@example.com", "password123"]
        mock_auth_controller_instance.login.return_value = {
            "token": "fake_token",
            "user": {"id": 1, "fullname": "Test User", "department": "gestion"},
        }

        result = mock_auth_view.login(mock_db)

        mock_ask.assert_any_call("Email")
        mock_ask.assert_any_call("Mot de passe", password=True)
        mock_auth_controller_instance.login.assert_called_once_with(
            mock_db, "test@example.com", "password123"
        )
        assert result is not None
        assert result["token"] == "fake_token"
        captured = capsys.readouterr()
        assert "Connexion réussie" in captured.out
        assert "Bienvenue Test User" in captured.out

    @patch("rich.prompt.Prompt.ask")
    def test_login_failure(
        self, mock_ask, mock_db, mock_auth_controller_instance, mock_auth_view, capsys
    ):
        """Teste une connexion échouée via AuthView."""
        mock_ask.side_effect = ["test@example.com", "wrongpassword"]
        mock_auth_controller_instance.login.return_value = None  # Échec de la connexion

        result = mock_auth_view.login(mock_db)

        mock_ask.assert_any_call("Email")
        mock_ask.assert_any_call("Mot de passe", password=True)
        mock_auth_controller_instance.login.assert_called_once_with(
            mock_db, "test@example.com", "wrongpassword"
        )
        assert result is None
        captured = capsys.readouterr()
        assert "Échec de la connexion" in captured.out

    @patch("epiceventsCRM.views.auth_view.clear_token")
    def test_logout(self, mock_clear_token, mock_auth_view, capsys):
        """Teste la déconnexion via AuthView."""
        mock_auth_view.logout()

        mock_clear_token.assert_called_once()
        captured = capsys.readouterr()
        assert "Déconnexion" in captured.out
        assert "Au revoir" in captured.out
