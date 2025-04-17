import pytest
from unittest.mock import Mock, patch

from epiceventsCRM.utils.permissions import (
    Department,
    get_department_permissions,
    has_permission,
    require_permission,
    PermissionError,
    COMMON_PERMISSIONS,
    DEPARTMENT_PERMISSIONS,
)
from epiceventsCRM.controllers.auth_controller import AuthController


class TestPermissions:
    """Tests unitaires pour les utilitaires de permissions."""

    def test_get_department_permissions(self):
        """Teste la récupération des permissions pour chaque département."""
        commercial_perms = get_department_permissions(Department.COMMERCIAL)
        support_perms = get_department_permissions(Department.SUPPORT)
        gestion_perms = get_department_permissions(Department.GESTION)

        # Vérifier que les permissions communes sont incluses
        assert COMMON_PERMISSIONS.issubset(commercial_perms)
        assert COMMON_PERMISSIONS.issubset(support_perms)
        assert COMMON_PERMISSIONS.issubset(gestion_perms)

        # Vérifier quelques permissions spécifiques
        assert "create_client" in commercial_perms
        assert "update_event" in support_perms
        assert "create_user" in gestion_perms
        assert "create_user" not in commercial_perms
        assert "delete_contract" in gestion_perms
        assert "delete_contract" not in support_perms

    def test_has_permission(self):
        """Teste la vérification de permission pour différents départements."""
        # Gestion a create_user
        assert has_permission(Department.GESTION, "create_user") is True
        # Commercial n'a pas create_user
        assert has_permission(Department.COMMERCIAL, "create_user") is False
        # Tous ont read_client
        assert has_permission(Department.SUPPORT, "read_client") is True
        assert has_permission(Department.COMMERCIAL, "read_client") is True
        # Permission inexistante
        assert has_permission(Department.GESTION, "non_existent_perm") is False


# --- Tests pour le décorateur require_permission --- #


# Classe factice pour simuler un contrôleur
class MockController:
    def __init__(self, auth_controller_mock):
        self.auth_controller = auth_controller_mock
        self.entity_name = "test_entity"  # Pour le formatage de permission

    @require_permission("read_test")
    def method_requires_read_test(self, token, *args):
        return "Success"

    @require_permission("write_test")
    def method_requires_write_test(self, token, *args):
        return "Success"

    @require_permission("read_{entity_name}")
    def method_requires_formatted_perm(self, token, *args):
        return "Success"

    @require_permission("some_perm")
    def method_without_token(self, *args):
        # Ce cas ne devrait pas arriver si le décorateur est bien utilisé
        return "Should Fail"

    @require_permission("some_perm")
    def method_with_token_kwarg(self, db, *, token):
        return "Success"


@pytest.fixture
def mock_auth_controller():
    """Crée un mock pour AuthController."""
    mock_auth = Mock(spec=AuthController)
    return mock_auth


@pytest.fixture
def mock_controller_instance(mock_auth_controller):
    """Crée une instance du contrôleur factice avec le mock AuthController."""
    return MockController(mock_auth_controller)


def test_require_permission_granted(mock_controller_instance, mock_auth_controller):
    """Teste le décorateur lorsque la permission est accordée."""
    mock_auth_controller.check_permission.return_value = True
    token = "valid_token"

    result = mock_controller_instance.method_requires_read_test(token)

    assert result == "Success"
    mock_auth_controller.check_permission.assert_called_once_with(token, "read_test")


def test_require_permission_denied(mock_controller_instance, mock_auth_controller):
    """Teste le décorateur lorsque la permission est refusée."""
    mock_auth_controller.check_permission.return_value = False
    # Simuler un retour de verify_token pour le message d'erreur
    mock_auth_controller.verify_token.return_value = {"sub": 123}
    token = "valid_token"

    with pytest.raises(PermissionError) as excinfo:
        mock_controller_instance.method_requires_write_test(token)

    mock_auth_controller.check_permission.assert_called_once_with(token, "write_test")
    assert "Permission refusée: write_test" in str(excinfo.value)
    assert excinfo.value.user_id == 123
    assert excinfo.value.permission == "write_test"


def test_require_permission_formatted(mock_controller_instance, mock_auth_controller):
    """Teste le décorateur avec un nom de permission formaté."""
    mock_auth_controller.check_permission.return_value = True
    token = "valid_token"

    result = mock_controller_instance.method_requires_formatted_perm(token)

    assert result == "Success"
    # Vérifier que la permission a été correctement formatée
    mock_auth_controller.check_permission.assert_called_once_with(token, "read_test_entity")


def test_require_permission_missing_token(mock_controller_instance):
    """Teste le décorateur lorsqu'aucun token n'est fourni (devrait échouer)."""
    # Appeler sans argument token
    with pytest.raises(PermissionError) as excinfo:
        mock_controller_instance.method_requires_read_test()

    assert "Token manquant" in str(excinfo.value)


def test_require_permission_missing_auth_controller():
    """Teste le décorateur sur une instance sans auth_controller."""

    class ControllerWithoutAuth:
        @require_permission("some_perm")
        def method(self, token):
            return "Success"

    instance = ControllerWithoutAuth()
    with pytest.raises(PermissionError) as excinfo:
        instance.method("some_token")

    assert "Contrôleur d'authentification manquant" in str(excinfo.value)


def test_require_permission_with_token_kwarg(mock_controller_instance, mock_auth_controller):
    """Teste le décorateur lorsque le token est passé comme keyword argument."""
    mock_auth_controller.check_permission.return_value = True
    token = "valid_token"
    mock_db = Mock()

    result = mock_controller_instance.method_with_token_kwarg(mock_db, token=token)

    assert result == "Success"
    mock_auth_controller.check_permission.assert_called_once_with(token, "some_perm")
