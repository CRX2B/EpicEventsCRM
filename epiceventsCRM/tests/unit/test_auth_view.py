import pytest
from unittest.mock import Mock, patch
from epiceventsCRM.views.auth_view import AuthView
from epiceventsCRM.controllers.auth_controller import AuthController


@pytest.fixture
def mock_auth_controller():
    """Fixture pour créer un mock du contrôleur d'authentification"""
    return Mock(spec=AuthController)


@pytest.fixture
def auth_view(mock_auth_controller):
    """Fixture pour créer une instance de AuthView avec un mock du contrôleur"""
    return AuthView(mock_auth_controller)


class TestAuthView:
    """Tests unitaires pour la vue d'authentification"""

    def test_login_success(self, auth_view, mock_auth_controller):
        """Test de la méthode login avec succès"""
        # Configuration du mock
        mock_auth_controller.login.return_value = {
            "user": {"fullname": "Test User"},
            "token": "test_token",
        }

        # Mock des entrées utilisateur
        with patch(
            "epiceventsCRM.views.auth_view.Prompt.ask", side_effect=["test@test.com", "password123"]
        ):
            # Mock de la sauvegarde du token
            with patch("epiceventsCRM.views.auth_view.save_token") as mock_save_token:
                # Mock de la session de base de données
                mock_db = Mock()

                # Appel de la méthode login
                result = auth_view.login(mock_db)

                # Vérifications
                assert result is not None
                assert result["user"]["fullname"] == "Test User"
                mock_auth_controller.login.assert_called_once_with(
                    mock_db, "test@test.com", "password123"
                )
                mock_save_token.assert_called_once_with("test_token")

    def test_login_failure(self, auth_view, mock_auth_controller):
        """Test de la méthode login avec échec"""
        # Configuration du mock
        mock_auth_controller.login.return_value = None

        # Mock des entrées utilisateur
        with patch(
            "epiceventsCRM.views.auth_view.Prompt.ask",
            side_effect=["test@test.com", "wrong_password"],
        ):
            # Mock de la session de base de données
            mock_db = Mock()

            # Appel de la méthode login
            result = auth_view.login(mock_db)

            # Vérifications
            assert result is None
            mock_auth_controller.login.assert_called_once_with(
                mock_db, "test@test.com", "wrong_password"
            )

    def test_logout(self, auth_view):
        """Test de la méthode logout"""
        # Mock de la suppression du token
        with patch("epiceventsCRM.views.auth_view.clear_token") as mock_clear_token:
            # Appel de la méthode logout
            auth_view.logout()

            # Vérification
            mock_clear_token.assert_called_once()
