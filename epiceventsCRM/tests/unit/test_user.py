import pytest
from unittest.mock import Mock, patch
from epiceventsCRM.models.models import User, Department
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.controllers.user_controller import UserController
from epiceventsCRM.views.user_view import UserView
from epiceventsCRM.utils.permissions import PermissionError
from epiceventsCRM.controllers.auth_controller import AuthController


@pytest.fixture
def mock_auth_controller():
    auth_controller = Mock(spec=AuthController)
    auth_controller.check_permission.return_value = True
    auth_controller.verify_token.return_value = {
        "sub": 1,
        "departement_id": 1,
        "permissions": ["create_user", "read_user", "update_user", "delete_user"]
    }
    return auth_controller


class MockUserDAO:
    def __init__(self, model):
        self.model = model
        self.users = []

    def create(self, db, user_data):
        user = User(**user_data)
        self.users.append(user)
        return user

    def get(self, db, user_id):
        return next((u for u in self.users if u.id == user_id), None)

    def get_all(self, db, page: int = 1, page_size: int = 10):
        # Calcul des indices de début et de fin pour la pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Récupération des utilisateurs pour la page demandée
        paginated_users = self.users[start_idx:end_idx]

        # Retourner les utilisateurs paginés et le nombre total
        return paginated_users, len(self.users)

    def get_by_email(self, db, email):
        return next((u for u in self.users if u.email == email), None)

    def update(self, db, user_id, user_data):
        user = self.get(db, user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
        return user

    def delete(self, db, user_id):
        user = self.get(db, user_id)
        if user:
            self.users.remove(user)
            return True
        return False


@pytest.fixture
def test_department():
    return Department(departement_name="commercial")


@pytest.fixture
def test_user_data(test_department):
    return {
        "fullname": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "departement_id": test_department.id,
    }


@pytest.fixture
def test_user(test_department):
    return User(
        fullname="Test User",
        email="test@example.com",
        password="password123",
        departement_id=test_department.id,
    )


@pytest.fixture
def mock_token_admin():
    return "fake_token"


class TestUserModel:
    """Tests unitaires pour le modèle User"""

    def test_user_creation(self):
        user = User(
            fullname="test_user", email="test@example.com", password="password123", departement_id=1
        )
        assert user.fullname == "test_user"
        assert user.email == "test@example.com"


class TestUserDAO:
    """Tests unitaires pour le DAO User"""

    def test_create_user(self, db_session, test_department):
        dao = UserDAO()
        user_data = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "departement_id": test_department.id,
        }
        user = dao.create(db_session, user_data)
        assert user.fullname == "Test User"
        assert user.email == "test@example.com"
        assert user.departement_id == test_department.id

    def test_get_user(self, db_session, test_department):
        dao = UserDAO()
        user_data = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "departement_id": test_department.id,
        }
        user = dao.create(db_session, user_data)
        retrieved_user = dao.get(db_session, user.id)
        assert retrieved_user.id == user.id
        assert retrieved_user.email == "test@example.com"

    def test_get_by_email(self, db_session, test_department):
        dao = UserDAO()
        user_data = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "departement_id": test_department.id,
        }
        user = dao.create(db_session, user_data)
        retrieved_user = dao.get_by_email(db_session, "test@example.com")
        assert retrieved_user.id == user.id
        assert retrieved_user.email == "test@example.com"

    def test_update_user(self, db_session, test_department):
        dao = UserDAO()
        user_data = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "departement_id": test_department.id,
        }
        user = dao.create(db_session, user_data)
        user = dao.get(db_session, user.id)  # Récupérer l'objet user complet
        updated_user = dao.update(
            db_session, user, {"fullname": "Updated User", "email": "updated@example.com"}
        )
        assert updated_user.fullname == "Updated User"
        assert updated_user.email == "updated@example.com"

    def test_delete_user(self, db_session, test_department):
        dao = UserDAO()
        user_data = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "departement_id": test_department.id,
        }
        user = dao.create(db_session, user_data)
        assert dao.delete(db_session, user.id) is True
        assert dao.get(db_session, user.id) is None


class TestUserController:
    def test_controller_create_user(
        self, db_session, test_department, mock_token_admin, mock_auth_controller
    ):
        dao = MockUserDAO(User)
        controller = UserController()
        controller.dao = dao
        controller.auth_controller = mock_auth_controller

        user_data = {
            "fullname": "Test User",
            "email": "test@example.com",
            "password": "password123",
        }

        # Configurer explicitement le mock pour la permission create_user
        mock_auth_controller.check_permission.return_value = True
        mock_auth_controller.verify_token.return_value = {
            "sub": 1,
            "departement_id": 1,
            "permissions": ["create_user", "read_user", "update_user", "delete_user"]
        }

        user = controller.create_with_department(
            token=mock_token_admin,
            db=db_session,
            user_data=user_data,
            department_id=test_department.id,
        )
        assert user.fullname == "Test User"
        assert user.email == "test@example.com"
        assert user.departement_id == test_department.id

    def test_get_user(self, db_session, test_user, mock_token_admin, mock_auth_controller):
        dao = MockUserDAO(User)
        dao.users.append(test_user)  # Ajouter l'utilisateur de test au mock DAO

        controller = UserController()
        controller.dao = dao
        controller.auth_controller = mock_auth_controller

        user = controller.get(token=mock_token_admin, db=db_session, entity_id=test_user.id)
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_all_users_with_pagination(
        self, db_session, test_department, mock_token_admin, mock_auth_controller
    ):
        dao = MockUserDAO(User)
        controller = UserController()
        controller.dao = dao
        controller.auth_controller = mock_auth_controller

        # Créer 15 utilisateurs de test
        for i in range(15):
            user_data = {
                "fullname": f"Test User {i}",
                "email": f"test{i}@example.com",
                "password": "password123",
                "departement_id": test_department.id,
            }
            dao.create(db_session, user_data)

        # Tester la première page (10 utilisateurs)
        users, total = controller.get_all(
            token=mock_token_admin, db=db_session, page=1, page_size=10
        )
        assert len(users) == 10
        assert total == 15
        assert users[0].fullname == "Test User 0"
        assert users[9].fullname == "Test User 9"

        # Tester la deuxième page (5 utilisateurs restants)
        users, total = controller.get_all(
            token=mock_token_admin, db=db_session, page=2, page_size=10
        )
        assert len(users) == 5
        assert total == 15
        assert users[0].fullname == "Test User 10"
        assert users[4].fullname == "Test User 14"


class TestUserView:
    def test_view_display_user(self, capsys):
        view = UserView()
        user = User(
            id=1,
            fullname="Test User",
            email="test@example.com",
            password="password123",
            departement_id=1,
        )

        view.display_item(user)
        captured = capsys.readouterr()
        assert "Test User" in captured.out
        assert "test@example.com" in captured.out
