import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from epiceventsCRM.models.models import Client, User, Department
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.views.client_view import ClientView
from epiceventsCRM.utils.auth import hash_password
from epiceventsCRM.utils.permissions import PermissionError
from epiceventsCRM.tests.mocks.mock_controllers import (
    MockAuthController,
    mock_token_commercial as get_mock_commercial_token_str,
    mock_token_gestion as get_mock_gestion_token_str,
)
from epiceventsCRM.tests.mocks.mock_dao import MockClientDAO
from epiceventsCRM.utils.validators import is_valid_email_format, is_valid_phone_format


@pytest.fixture
def test_department():
    return Department(departement_name="commercial")


@pytest.fixture
def test_commercial(test_department):
    user = User(
        id=1,
        fullname="Commercial Test",
        email="commercial@test.com",
        password="password123",
        departement_id=test_department.id,
    )
    return user


@pytest.fixture
def test_client(test_commercial):
    client = Client(
        id=101,
        fullname="Test Client",
        email="client@test.com",
        phone_number="0123456789",
        enterprise="Test Company",
        sales_contact_id=test_commercial.id,
    )
    return client


@pytest.fixture
def test_client_data(test_commercial):
    return {
        "fullname": "Test Client",
        "email": "client@test.com",
        "phone_number": "0123456789",
        "enterprise": "Test Company",
    }


class TestClientModel:
    """Tests unitaires pour le modèle Client"""

    def test_client_creation(self):
        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number="0123456789",
            enterprise="Test Company",
        )
        assert client.fullname == "Client Test"
        assert client.email == "client@test.com"
        assert client.enterprise == "Test Company"


class TestClientController:
    @pytest.fixture(autouse=True)
    def setup_controller(self, mock_auth_controller_fixture):
        """Injecte les mocks dans une instance du contrôleur pour les tests de cette classe."""
        self.mock_dao = MockClientDAO()
        self.mock_auth_controller = mock_auth_controller_fixture
        self.mock_dao.reset_mocks()
        self.mock_auth_controller.reset_mocks()

        self.controller = ClientController()
        self.controller.dao = self.mock_dao
        self.controller.auth_controller = self.mock_auth_controller

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_controller_create_client_success(self, mock_verify, db_session, test_client_data):
        mock_verify.return_value = {"sub": 1, "department": "commercial"}
        token = get_mock_commercial_token_str()
        self.mock_auth_controller.check_permission.return_value = True

        client = self.controller.create(
            token=token, db=db_session, client_data=test_client_data.copy()
        )

        assert client is not None
        mock_verify.assert_called_with(token)
        self.mock_dao.create_client.assert_called_once()
        call_args = self.mock_dao.create_client.call_args
        assert call_args.args[1]["sales_contact_id"] == 1
        self.mock_auth_controller.check_permission.assert_called_with(token, "create_client")

    @pytest.mark.parametrize(
        "invalid_data, expected_error_msg_part",
        [
            (
                {"fullname": "Test", "phone_number": "123", "enterprise": "Comp"},
                "Champ obligatoire manquant ou vide: email",
            ),
            (
                {
                    "fullname": "Test",
                    "email": "invalid-email",
                    "phone_number": "1234567",
                    "enterprise": "Comp",
                },
                "Format d'email invalide.",
            ),
            (
                {
                    "fullname": "Test",
                    "email": "test@valid.com",
                    "phone_number": "abc",
                    "enterprise": "Comp",
                },
                "Format de numéro de téléphone invalide.",
            ),
            (
                {
                    "fullname": "a" * 101,
                    "email": "test@valid.com",
                    "phone_number": "1234567",
                    "enterprise": "Comp",
                },
                "Nom complet trop long",
            ),
            (
                {
                    "fullname": "Test",
                    "email": "test@valid.com",
                    "phone_number": "1234567",
                    "enterprise": "b" * 101,
                },
                "Nom d'entreprise trop long",
            ),
        ],
    )
    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    @patch("epiceventsCRM.controllers.client_controller.capture_message")
    def test_create_client_validation_errors(
        self, mock_capture, mock_verify, invalid_data, expected_error_msg_part, db_session
    ):
        mock_verify.return_value = {"sub": 1, "department": "commercial"}
        token = get_mock_commercial_token_str()
        self.mock_auth_controller.check_permission.return_value = True

        client = self.controller.create(token, db_session, invalid_data)

        assert client is None
        self.mock_dao.create_client.assert_not_called()
        assert expected_error_msg_part in mock_capture.call_args[0][0]
        assert mock_capture.call_args[1]["level"] == "warning"

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_create_client_permission_denied(self, mock_verify, db_session, test_client_data):
        mock_verify.return_value = {"sub": 99, "department": "support"}
        token = "support_token"
        self.mock_auth_controller.check_permission.return_value = False

        with pytest.raises(PermissionError):
            self.controller.create(token, db_session, test_client_data.copy())

        self.mock_auth_controller.check_permission.assert_called_with(token, "create_client")
        self.mock_dao.create_client.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_success_owner(self, mock_verify, db_session, test_client):
        user_id = test_client.sales_contact_id
        mock_verify.return_value = {"sub": user_id, "department": "commercial"}
        token = get_mock_commercial_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        self.mock_dao.get = Mock(return_value=test_client)
        self.mock_dao.update_client = Mock(return_value=test_client)

        update_data = {
            "fullname": "Updated Client Name",
            "email": "update@valid.com",
            "phone_number": "987654321",
        }
        result = self.controller.update_client(db_session, token, test_client.id, update_data)

        assert result is not None
        self.mock_auth_controller.check_permission.assert_called_with(token, "update_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_dao.update_client.assert_called_once_with(db_session, test_client.id, update_data)

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_success_gestion(self, mock_verify, db_session, test_client):
        mock_verify.return_value = {"sub": 50, "department": "gestion"}
        token = get_mock_gestion_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        self.mock_dao.get = Mock(return_value=test_client)
        self.mock_dao.update_client = Mock(return_value=test_client)

        update_data = {"enterprise": "Gestion Updated Enterprise"}
        result = self.controller.update_client(db_session, token, test_client.id, update_data)

        assert result is not None
        self.mock_auth_controller.check_permission.assert_called_with(token, "update_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_dao.update_client.assert_called_once_with(db_session, test_client.id, update_data)

    @pytest.mark.parametrize(
        "invalid_data, expected_error_msg_part",
        [
            ({"email": "invalid-email"}, "Format d'email invalide."),
            ({"phone_number": "abc"}, "Format de numéro de téléphone invalide."),
            ({"fullname": "a" * 101}, "Nom complet trop long"),
            ({"enterprise": "b" * 101}, "Nom d'entreprise trop long"),
        ],
    )
    @patch("epiceventsCRM.controllers.client_controller.capture_message")
    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_validation_errors(
        self,
        mock_verify,
        mock_capture,
        invalid_data,
        expected_error_msg_part,
        db_session,
        test_client,
    ):
        user_id = test_client.sales_contact_id
        mock_verify.return_value = {"sub": user_id, "department": "commercial"}
        token = get_mock_commercial_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        self.mock_dao.get = Mock(return_value=test_client)
        self.mock_dao.update_client = Mock()

        result = self.controller.update_client(db_session, token, test_client.id, invalid_data)

        assert result is None
        self.mock_dao.update_client.assert_not_called()
        mock_capture.assert_called_once()
        assert expected_error_msg_part in mock_capture.call_args[0][0]
        assert mock_capture.call_args[1]["level"] == "warning"

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_commercial_denied_other(self, mock_verify, db_session, test_client):
        other_commercial_id = 99
        mock_verify.return_value = {"sub": other_commercial_id, "department": "commercial"}
        token = "other_commercial_token"
        self.mock_auth_controller.check_permission.return_value = True
        self.mock_dao.get.return_value = test_client

        update_data = {"fullname": "Attempt Update"}
        result = self.controller.update_client(db_session, token, test_client.id, update_data)

        assert result is None
        self.mock_auth_controller.check_permission.assert_called_with(token, "update_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_dao.update_client.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_permission_denied_base(self, mock_verify, db_session, test_client):
        mock_verify.return_value = {"sub": 10, "department": "support"}
        token = "support_token"
        self.mock_auth_controller.check_permission.return_value = False

        update_data = {"fullname": "Attempt Update"}
        with pytest.raises(PermissionError):
            self.controller.update_client(db_session, token, test_client.id, update_data)

        self.mock_auth_controller.check_permission.assert_called_with(token, "update_client")
        self.mock_dao.get.assert_not_called()
        self.mock_dao.update_client.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_commercial_success(self, mock_verify, db_session, test_client):
        gestion_user_id = 50
        new_commercial_id = 5
        mock_verify.return_value = {"sub": gestion_user_id, "department": "gestion"}
        token = get_mock_gestion_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        self.mock_dao.get = Mock(return_value=test_client)
        self.mock_dao.update_commercial = Mock(return_value=test_client)

        result = self.controller.update_client_commercial(
            token, db_session, test_client.id, new_commercial_id
        )

        assert result is not None
        self.mock_auth_controller.check_permission.assert_called_with(token, "update_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)
        self.mock_dao.update_commercial.assert_called_once_with(
            db_session, test_client, new_commercial_id
        )

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_update_client_commercial_client_not_found(self, mock_verify, db_session):
        gestion_user_id = 50
        new_commercial_id = 5
        mock_verify.return_value = {"sub": gestion_user_id, "department": "gestion"}
        token = get_mock_gestion_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        self.mock_dao.get = Mock(return_value=None)

        client_id = 999
        result = self.controller.update_client_commercial(
            token, db_session, client_id, new_commercial_id
        )

        assert result is None
        self.mock_auth_controller.check_permission.assert_called_with(token, "update_client")
        self.mock_dao.get.assert_called_once_with(db_session, client_id)
        self.mock_dao.update_commercial.assert_not_called()

    @patch("epiceventsCRM.controllers.client_controller.verify_token")
    def test_get_my_clients_invalid_token(self, mock_verify, db_session):
        mock_verify.return_value = None
        token = "invalid_token"
        self.mock_auth_controller.check_permission.return_value = True

        result = self.controller.get_my_clients(db_session, token)
        assert result == []
        mock_verify.assert_called_once_with(token)
        self.mock_dao.get_by_sales_contact.assert_not_called()

    def test_get_client_permission_ok(self, db_session, test_client):
        token = get_mock_commercial_token_str()
        self.mock_auth_controller.check_permission.return_value = True
        self.mock_dao.get = Mock(return_value=test_client)

        client_result = self.controller.get_client(db_session, token, test_client.id)

        assert client_result is not None
        assert client_result.id == test_client.id
        self.mock_auth_controller.check_permission.assert_called_with(token, "read_client")
        self.mock_dao.get.assert_called_once_with(db_session, test_client.id)

    def test_get_client_permission_denied(self, db_session, test_client):
        token = "support_token"
        self.mock_auth_controller.check_permission.return_value = False

        with pytest.raises(PermissionError):
            self.controller.get_client(db_session, token, test_client.id)

        self.mock_auth_controller.check_permission.assert_called_with(token, "read_client")
        self.mock_dao.get.assert_not_called()


class TestClientView:
    def test_view_display_client(self, capsys):
        view = ClientView()
        client = Client(
            id=1,
            fullname="Test Client",
            email="client@test.com",
            phone_number="0123456789",
            enterprise="Test Company",
            sales_contact_id=1,
        )

        view.display_item(client)
        captured = capsys.readouterr()
        assert "Test Client" in captured.out
        assert "client@test.com" in captured.out
        assert "Test Company" in captured.out
