import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from epiceventsCRM.models.models import User, Department
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.views.user_view import UserView
from epiceventsCRM.controllers.user_controller import UserController
from epiceventsCRM.controllers.auth_controller import AuthController
from epiceventsCRM.tests.mocks.mock_dao import MockUserDAO, MockDepartmentDAO
from epiceventsCRM.tests.mocks.mock_controllers import (
    MockAuthController,
    mock_token_gestion as get_mock_gestion_token_str,
    mock_token_commercial as get_mock_commercial_token_str,
)
from epiceventsCRM.utils.permissions import (
    PermissionError,
    Department as DepartmentEnum,
    has_permission,
)
from sqlalchemy.exc import IntegrityError
from epiceventsCRM.utils.validators import is_valid_email_format
import unittest.mock
from unittest.mock import patch, Mock
import copy


@pytest.fixture
def test_department():
    return Department(id=3, departement_name="gestion")


@pytest.fixture
def test_user_data(test_department):
    return {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "departement_id": test_department.id,
    }


@pytest.fixture
def test_user(test_user_data, test_department):
    user = User(**test_user_data)
    user.id = 1
    user.department = test_department
    return user


class TestUserModel:
    """Tests unitaires pour le modèle User"""

    def test_user_creation(self):
        """Teste la création d'une instance User."""
        user = User(fullname="John Doe", email="john@example.com", password="securepassword")
        assert user.fullname == "John Doe"
        assert user.email == "john@example.com"

    def test_user_representation(self, test_user):
        """Teste la représentation textuelle de l'utilisateur."""
        assert (
            repr(test_user) == f"User(fullname='{test_user.fullname}', email='{test_user.email}')"
        )


class TestUserDAO:
    """Tests unitaires pour le DAO User"""

    @pytest.fixture
    def user_dao(self):
        return UserDAO()

    def test_create_user(self, user_dao, db_session, test_user_data):
        """Test de création d'un utilisateur via DAO."""
        user = user_dao.create(db_session, test_user_data)
        assert user is not None
        assert user.id is not None
        assert user.fullname == test_user_data["fullname"]
        assert user.password != test_user_data["password"]

    def test_get(self, user_dao, db_session, test_user):
        """Test de récupération d'un utilisateur par ID en utilisant la méthode get."""
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        retrieved_user = user_dao.get(db_session, test_user.id)
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.email == test_user.email

    def test_authenticate_user(self, user_dao, db_session, test_user_data):
        """Test d'authentification d'un utilisateur."""
        user_dao.create(db_session, test_user_data)
        authenticated_user = user_dao.authenticate(
            db_session, test_user_data["email"], test_user_data["password"]
        )
        assert authenticated_user is not None
        assert authenticated_user.email == test_user_data["email"]

        failed_auth = user_dao.authenticate(db_session, test_user_data["email"], "wrongpassword")
        assert failed_auth is None

    def test_update_user_password(self, user_dao, db_session, test_user):
        """Test de mise à jour du mot de passe."""
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        new_password = "newpassword456"
        updated_user = user_dao.update_password(db_session, test_user.id, new_password)
        assert updated_user is not None

        reauthenticated_user = user_dao.authenticate(db_session, test_user.email, new_password)
        assert reauthenticated_user is not None
        assert reauthenticated_user.id == test_user.id


class TestUserView:
    """Tests unitaires pour la vue User"""

    def test_display_user(self, test_user, capsys):
        """Test de l'affichage des détails d'un utilisateur."""
        view = UserView()
        view.display_item(test_user)
        captured = capsys.readouterr()
        assert test_user.fullname in captured.out
        assert test_user.email in captured.out
        assert test_user.department.departement_name in captured.out

    def test_display_users(self, test_user, capsys):
        """Test de l'affichage d'une liste d'utilisateurs."""
        view = UserView()
        users_list = [test_user, test_user]
        view.display_items(users_list)
        captured = capsys.readouterr()
        assert "Liste des utilisateurs" in captured.out
        assert test_user.fullname in captured.out
        assert test_user.email in captured.out
        assert "Nom complet" in captured.out
        assert "Département" in captured.out

    def test_controller_update_user_department(self, setup_user_controller_mocks, test_user):
        """Teste la mise à jour du département via le contrôleur."""
        controller, dao, dep_dao, mock_auth = setup_user_controller_mocks
        dao._data[test_user.id] = test_user
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.get.return_value = test_user
        valid_department = Department(id=2, departement_name="support")
        dep_dao.get.return_value = valid_department
        dao.update.return_value = test_user

        update_data = {"departement_id": valid_department.id}
        updated_user = controller.update(token, None, test_user.id, update_data)

        assert updated_user is not None
        mock_auth.check_permission.assert_called_with(token, "update_user")
        dao.get.assert_called_once_with(None, test_user.id)
        dao.update.assert_called_once_with(None, test_user, update_data)

        assert not hasattr(dao, "assign_department")

    def test_controller_delete_user(self, setup_user_controller_mocks, test_user):
        """Teste la suppression réussie d'un utilisateur."""
        controller, dao, _, mock_auth = setup_user_controller_mocks
        dao._data[test_user.id] = test_user
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.delete.return_value = True

        result = controller.delete(token, None, test_user.id)

        assert result is True
        mock_auth.check_permission.assert_called_with(token, "delete_user")
        dao.delete.assert_called_once_with(None, test_user.id)


@pytest.fixture
def setup_user_controller_mocks():
    """Fixture pour configurer les mocks pour UserController."""
    mock_user_dao = MockUserDAO()
    mock_department_dao = MockDepartmentDAO()
    mock_auth_controller = MockAuthController()
    mock_department_dao._data[1] = Department(id=1, departement_name="commercial")
    mock_department_dao._data[2] = Department(id=2, departement_name="support")
    mock_department_dao._data[3] = Department(id=3, departement_name="gestion")

    controller = UserController()
    controller.dao = mock_user_dao
    controller.department_dao = mock_department_dao
    controller.auth_controller = mock_auth_controller
    return controller, mock_user_dao, mock_department_dao, mock_auth_controller


class TestUserController:
    """Tests unitaires pour UserController."""

    @pytest.fixture(autouse=True)
    def setup_controller(self, mock_auth_controller_fixture):
        """Injecte les mocks dans une instance du contrôleur pour les tests de cette classe."""
        self.mock_dao = MockUserDAO()
        self.mock_department_dao = MockDepartmentDAO()
        self.mock_auth_controller = mock_auth_controller_fixture
        self.mock_dao.reset_mocks()
        self.mock_department_dao.reset_mocks()
        self.mock_auth_controller.reset_mocks()

        self.controller = UserController()
        self.controller.dao = self.mock_dao
        self.controller.department_dao = self.mock_department_dao
        self.controller.auth_controller = self.mock_auth_controller

    def test_controller_create_user_success(self, test_user_data):
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        created_user_obj = User(**test_user_data)
        created_user_obj.id = 1
        dao.create.return_value = created_user_obj
        department_id = test_user_data["departement_id"]

        created_user = controller.create_with_department(
            token, None, test_user_data.copy(), department_id
        )

        assert created_user is not None
        assert created_user.id == 1
        mock_auth.check_permission.assert_called_with(token, "create_user")
        dao.create.assert_called_once()

    @pytest.mark.parametrize(
        "invalid_data, expected_error_part",
        [
            ({"fullname": "Test", "password": "pass"}, "Champ obligatoire manquant ou vide: email"),
            (
                {"fullname": "Test", "email": "invalid-email", "password": "pass"},
                "Format d'email invalide.",
            ),
            (
                {"fullname": "a" * 101, "email": "test@valid.com", "password": "pass"},
                "Nom complet trop long",
            ),
        ],
    )
    @patch("epiceventsCRM.controllers.user_controller.capture_message")
    def test_controller_create_user_validation_errors(
        self, mock_capture, invalid_data, expected_error_part, test_user_data
    ):
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        department_id = test_user_data["departement_id"]
        final_data = invalid_data

        with pytest.raises(ValueError) as excinfo:
            controller.create_with_department(token, None, final_data, department_id)

        assert expected_error_part in str(excinfo.value)
        mock_capture.assert_called_once()
        assert expected_error_part in mock_capture.call_args[0][0]
        dao.create.assert_not_called()

    def test_controller_create_user_invalid_department(self, test_user_data):
        """Teste la création avec un ID de département invalide."""
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller

        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        invalid_department_id = 99

        mock_integrity_error = IntegrityError(
            "(IntegrityError) violates foreign key constraint",
            params={},
            orig=Exception("violates foreign key constraint...departments"),
        )
        dao.create.side_effect = mock_integrity_error

        with pytest.raises(ValueError) as excinfo:
            controller.create_with_department(token, None, test_user_data, invalid_department_id)

        assert f"Département ID {invalid_department_id} invalide" in str(excinfo.value)
        mock_auth.check_permission.assert_called_with(token, "create_user")
        dao.create.assert_called_once()

    def test_controller_update_user_success(self, test_user):
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.get.return_value = test_user
        updated_user_mock = User(
            id=test_user.id,
            fullname="Updated Name",
            email="updated@valid.com",
            password=test_user.password,
            departement_id=test_user.departement_id,
        )
        update_data = {"fullname": "Updated Name", "email": "updated@valid.com"}

        with patch(
            "epiceventsCRM.controllers.base_controller.BaseController.update",
            return_value=updated_user_mock,
        ) as mock_super_update:
            updated_user_result = controller.update(token, None, test_user.id, update_data)

            assert updated_user_result is not None
            assert updated_user_result.fullname == "Updated Name"
            mock_super_update.assert_called_once_with(token, None, test_user.id, update_data)

    @pytest.mark.parametrize(
        "invalid_data, expected_error_part",
        [
            ({"email": "invalid-email"}, "Format d'email invalide."),
            ({"fullname": "a" * 101}, "Nom complet trop long"),
        ],
    )
    @patch("epiceventsCRM.controllers.user_controller.capture_message")
    def test_controller_update_user_validation_errors(
        self, mock_capture, invalid_data, expected_error_part, test_user
    ):
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.get.return_value = test_user

        with pytest.raises(ValueError) as excinfo:
            controller.update(token, None, test_user.id, invalid_data)

        assert expected_error_part in str(excinfo.value)
        mock_capture.assert_called_once()
        assert expected_error_part in mock_capture.call_args[0][0]
        dao.update.assert_not_called()

    def test_controller_update_user_department_success(self, test_user):
        """Teste la mise à jour du département via le contrôleur."""
        controller = self.controller
        dao = self.mock_dao
        dep_dao = self.mock_department_dao
        mock_auth = self.mock_auth_controller

        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.get.return_value = test_user
        dao.get.side_effect = None
        valid_department = Department(id=2, departement_name="support")
        dep_dao.get.return_value = valid_department
        dep_dao.get.side_effect = None
        dao.update.return_value = test_user
        dao.update.side_effect = None

        update_data = {"departement_id": valid_department.id}
        updated_user = controller.update(token, None, test_user.id, update_data)

        assert updated_user is not None
        mock_auth.check_permission.assert_called_with(token, "update_user")
        dao.get.assert_called_once_with(None, test_user.id)
        dao.update.assert_called_once_with(None, test_user, update_data)
        assert not hasattr(dao, "assign_department")

    def test_controller_delete_user_success(self, test_user):
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller
        dao.get = Mock(return_value=test_user)
        dao.delete = Mock(return_value=True)
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()

        result = controller.delete(token, None, test_user.id)

        assert result is True
        mock_auth.check_permission.assert_called_with(token, "delete_user")
        dao.get.assert_called_once_with(None, test_user.id)
        dao.delete.assert_called_once_with(None, test_user.id)

    def test_controller_delete_user_internal_get_fails(self):
        """Teste le cas où get réussit mais dao.delete retourne False"""
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        user_id_not_exist = 999
        dao.get.return_value = None

        result = controller.delete(token, None, user_id_not_exist)

        assert result is False
        mock_auth.check_permission.assert_called_with(token, "delete_user")
        dao.get.assert_called_once_with(None, user_id_not_exist)
        dao.delete.assert_not_called()

    def test_controller_delete_user_dao_fails(self, test_user):
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller
        dao.get = Mock(return_value=test_user)
        dao.delete = Mock(return_value=False)
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()

        result = controller.delete(token, None, test_user.id)

        assert result is False
        mock_auth.check_permission.assert_called_with(token, "delete_user")
        dao.get.assert_called_once_with(None, test_user.id)
        dao.delete.assert_called_once_with(None, test_user.id)


@pytest.fixture
def auth_controller_instance():
    controller = AuthController()
    controller.user_dao = Mock(spec=UserDAO)
    return controller


@pytest.fixture
def mock_db():
    return Mock()


class TestAuthControllerLogic:

    @patch("epiceventsCRM.controllers.auth_controller.capture_message")
    def test_login_invalid_credentials(self, mock_capture, auth_controller_instance, mock_db):
        auth_controller_instance.user_dao.authenticate.return_value = None
        result = auth_controller_instance.login(mock_db, "wrong@test.com", "wrongpass")
        assert result is None
        auth_controller_instance.user_dao.authenticate.assert_called_once_with(
            mock_db, "wrong@test.com", "wrongpass"
        )
        mock_capture.assert_called_with(
            "Échec de connexion pour l'email: wrong@test.com", level="warning"
        )

    @patch("epiceventsCRM.controllers.auth_controller.capture_message")
    def test_login_user_without_department(self, mock_capture, auth_controller_instance, mock_db):
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "nodep@test.com"
        mock_user.fullname = "No Department"
        mock_user.department = None
        auth_controller_instance.user_dao.authenticate.return_value = mock_user

        result = auth_controller_instance.login(mock_db, "nodep@test.com", "password")
        assert result is None
        mock_capture.assert_called_with(
            "Utilisateur sans département: nodep@test.com", level="error"
        )

    @patch("epiceventsCRM.controllers.auth_controller.verify_token")
    @patch("epiceventsCRM.controllers.auth_controller.capture_message")
    def test_check_permission_invalid_token(
        self, mock_capture, mock_verify, auth_controller_instance
    ):
        mock_verify.return_value = None
        result = auth_controller_instance.check_permission("invalid_token", "some_permission")
        assert result is False
        mock_verify.assert_called_once_with("invalid_token")
        mock_capture.assert_called_with(
            "Vérification de permission avec un token invalide", level="warning"
        )

    @patch("epiceventsCRM.controllers.auth_controller.verify_token")
    @patch("epiceventsCRM.controllers.auth_controller.capture_message")
    def test_check_permission_invalid_department_in_token(
        self, mock_capture, mock_verify, auth_controller_instance
    ):
        mock_verify.return_value = {"sub": 1, "department": "invalid_dept"}
        result = auth_controller_instance.check_permission(
            "valid_token_invalid_dept", "some_permission"
        )
        assert result is False
        mock_capture.assert_called_with(
            "Département invalide dans le token: invalid_dept",
            level="error",
            extra=unittest.mock.ANY,
        )

    @patch("epiceventsCRM.controllers.auth_controller.verify_token")
    @patch("epiceventsCRM.controllers.auth_controller.has_permission")
    @patch("epiceventsCRM.controllers.auth_controller.capture_message")
    def test_check_permission_denied(
        self, mock_capture, mock_has_perm, mock_verify, auth_controller_instance
    ):
        mock_verify.return_value = {"sub": 1, "department": "commercial"}
        mock_has_perm.return_value = False

        result = auth_controller_instance.check_permission("valid_token", "admin_permission")
        assert result is False
        mock_has_perm.assert_called_once_with(DepartmentEnum.COMMERCIAL, "admin_permission")
        mock_capture.assert_called_with(
            "Accès refusé: utilisateur 1 a tenté d'accéder à admin_permission",
            level="warning",
            extra={
                "user_id": 1,
                "department": "commercial",
                "permission": "admin_permission",
            },
        )
