import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from epiceventsCRM.models.models import User, Department
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.views.user_view import UserView
from epiceventsCRM.controllers.user_controller import UserController
from epiceventsCRM.tests.mocks.mock_dao import MockUserDAO, MockDepartmentDAO
from epiceventsCRM.tests.mocks.mock_controllers import (
    MockAuthController,
    mock_token_gestion as get_mock_gestion_token_str,
    mock_token_commercial as get_mock_commercial_token_str,
)
from epiceventsCRM.utils.permissions import PermissionError


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
        assert user.password != test_user_data["password"]  # Le mot de passe doit être hashé

    def test_get(self, user_dao, db_session, test_user):
        """Test de récupération d'un utilisateur par ID en utilisant la méthode get."""
        # Ajouter l'utilisateur de test à la session
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)  # Pour obtenir l'ID auto-incrémenté si besoin

        retrieved_user = user_dao.get(db_session, test_user.id)
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.email == test_user.email

    def test_authenticate_user(self, user_dao, db_session, test_user_data):
        """Test d'authentification d'un utilisateur."""
        user_dao.create(db_session, test_user_data)  # Créer l'utilisateur
        authenticated_user = user_dao.authenticate(
            db_session, test_user_data["email"], test_user_data["password"]
        )
        assert authenticated_user is not None
        assert authenticated_user.email == test_user_data["email"]

        # Tester avec mauvais mot de passe
        failed_auth = user_dao.authenticate(db_session, test_user_data["email"], "wrongpassword")
        assert failed_auth is None

    def test_update_user_password(self, user_dao, db_session, test_user):
        """Test de mise à jour du mot de passe."""
        # Ajouter l'utilisateur de test à la session
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

        new_password = "newpassword456"
        updated_user = user_dao.update_password(db_session, test_user.id, new_password)
        assert updated_user is not None

        # Vérifier la nouvelle authentification
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
        users_list = [test_user, test_user]  # Afficher le même utilisateur deux fois
        view.display_items(users_list)
        captured = capsys.readouterr()
        assert "Liste des utilisateurs" in captured.out
        assert test_user.fullname in captured.out
        assert test_user.email in captured.out
        # Vérifier que l'en-tête est présent
        assert "Nom complet" in captured.out
        assert "Département" in captured.out

    def test_controller_update_user_department(self, setup_user_controller_mocks, test_user):
        """Teste la mise à jour du département via le contrôleur."""
        controller, dao, dep_dao, mock_auth = setup_user_controller_mocks
        dao._data[test_user.id] = test_user
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.get.return_value = test_user  # Simuler utilisateur trouvé
        valid_department = Department(id=2, departement_name="support")
        dep_dao.get.return_value = valid_department
        dao.update.return_value = test_user  # Simule succès de la mise à jour via update

        update_data = {"departement_id": valid_department.id}
        # Appeler la méthode standard update du contrôleur
        updated_user = controller.update(token, None, test_user.id, update_data)

        assert updated_user is not None
        mock_auth.check_permission.assert_called_with(token, "update_user")
        dao.get.assert_called_once_with(None, test_user.id)

        dao.update.assert_called_once_with(None, test_user, update_data)

        assert not hasattr(dao, "assign_department")

    def test_controller_delete_user(self, setup_user_controller_mocks, test_user):
        """Teste la suppression réussie d'un utilisateur."""
        controller, dao, _, mock_auth = setup_user_controller_mocks
        # Ajouter l'utilisateur au _data pour que controller.delete le trouve via dao.get
        dao._data[test_user.id] = test_user
        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.delete.return_value = True  # Simuler succès suppression

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
    # Pré-remplir le mock department dao
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
        self.mock_dao = MockUserDAO()  # Utilisation directe de MockUserDAO
        self.mock_department_dao = MockDepartmentDAO()  # Ajouter le mock département ici aussi
        self.mock_auth_controller = mock_auth_controller_fixture
        # Réinitialiser les mocks
        self.mock_dao.reset_mocks()
        self.mock_department_dao.reset_mocks()
        self.mock_auth_controller.reset_mocks()

        self.controller = UserController()  # Initialisation normale
        # Remplacer les attributs par les mocks
        self.controller.dao = self.mock_dao
        self.controller.department_dao = self.mock_department_dao
        self.controller.auth_controller = self.mock_auth_controller

    def test_controller_create_user(self, test_user_data):
        """Teste la création réussie d'un utilisateur via le contrôleur."""
        controller = self.controller
        dao = self.mock_dao
        dep_dao = self.mock_department_dao
        mock_auth = self.mock_auth_controller

        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()

        # Configurer le mock create du DAO user
        dao.create.return_value = User(**test_user_data)
        # Configurer le mock get du DAO département ET le _data
        department_id = test_user_data["departement_id"]
        department = Department(id=department_id, departement_name="gestion")
        dep_dao._data[department_id] = department  # Ajouter au dictionnaire interne
        dep_dao.get.return_value = department

        created_user = controller.create_with_department(token, None, test_user_data, department_id)

        assert created_user is not None
        mock_auth.check_permission.assert_called_with(token, "create_user")
        dep_dao.get.assert_called_once_with(None, department_id)
        dao.create.assert_called_once()
        call_args, call_kwargs = dao.create.call_args
        assert call_args[1]["email"] == test_user_data["email"]

    def test_controller_create_user_invalid_department(self, test_user_data):
        """Teste la création avec un ID de département invalide."""
        controller = self.controller
        dao = self.mock_dao
        dep_dao = self.mock_department_dao
        mock_auth = self.mock_auth_controller

        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        invalid_department_id = 99

        dep_dao.get.return_value = None
        dep_dao.get.side_effect = None  # Assurer que return_value est utilisé

        with pytest.raises(ValueError) as excinfo:
            controller.create_with_department(token, None, test_user_data, invalid_department_id)
        assert f"Département ID {invalid_department_id} invalide" in str(excinfo.value)

        mock_auth.check_permission.assert_called_with(token, "create_user")
        dep_dao.get.assert_called_once_with(None, invalid_department_id)
        dao.create.assert_not_called()

    def test_controller_update_user(self, test_user):
        """Teste la mise à jour réussie d'un utilisateur."""
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller

        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.get.return_value = test_user
        dao.get.side_effect = None
        dao.update.return_value = test_user
        dao.update.side_effect = None

        update_data = {"fullname": "Updated Name"}
        updated_user = controller.update(token, None, test_user.id, update_data)

        assert updated_user is not None
        mock_auth.check_permission.assert_called_with(token, "update_user")
        dao.get.assert_called_once_with(None, test_user.id)
        dao.update.assert_called_once_with(None, test_user, update_data)

    def test_controller_update_user_department(self, test_user):
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
        # Vérifier que la méthode update du DAO est appelée avec les bonnes données
        dao.update.assert_called_once_with(None, test_user, update_data)
        assert not hasattr(dao, "assign_department")

    def test_controller_delete_user(self, test_user):
        """Teste la suppression réussie d'un utilisateur."""
        controller = self.controller
        dao = self.mock_dao
        mock_auth = self.mock_auth_controller

        mock_auth.check_permission.return_value = True
        token = get_mock_gestion_token_str()
        dao.delete.return_value = True
        dao.delete.side_effect = None
        # Il faut aussi mocker dao.get qui est appelé avant delete dans le contrôleur
        dao.get.return_value = test_user
        dao.get.side_effect = None

        result = controller.delete(token, None, test_user.id)

        assert result is True
        mock_auth.check_permission.assert_called_with(token, "delete_user")
        dao.get.assert_called_once_with(None, test_user.id)  # Vérifier l'appel à get
        dao.delete.assert_called_once_with(None, test_user.id)
