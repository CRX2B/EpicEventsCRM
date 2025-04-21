from typing import Dict, Optional
from datetime import datetime, timezone
from unittest.mock import Mock


class MockAuthController:
    """Mock du contrôleur d'authentification avec suivi des appels"""

    def __init__(self, department=None):
        self.users = {
            "commercial": {
                "id": 1,
                "department": "commercial",
                "token": "commercial_token",
                "permissions": [
                    "create_client",
                    "read_client",
                    "update_client",
                    "create_event",
                    "read_event",
                    "read_contract",
                ],
            },
            "gestion": {
                "id": 2,
                "department": "gestion",
                "token": "gestion_token",
                "permissions": [
                    "create_contract",
                    "read_contract",
                    "update_contract",
                    "delete_contract",
                    "read_client",
                ],
            },
            "support": {
                "id": 3,
                "department": "support",
                "token": "support_token",
                "permissions": [
                    "create_event",
                    "read_event",
                    "update_event",
                    "read_client",
                    "read_contract",
                ],
            },
        }
        self.current_user_department = department
        self.current_user = self.users.get(department) if department else None

        self.check_permission = Mock()
        self._original_verify_token = self._verify_token_impl
        self.verify_token = Mock(side_effect=self._original_verify_token)

    def _check_permission_impl(self, token, permission):
        """Simule la vérification de permission."""
        payload = self._verify_token_impl(token)
        if not payload:
            return False
        has_perm = permission in payload.get("permissions", [])
        return has_perm

    def _verify_token_impl(self, token):
        """Simule la vérification d'un token."""
        for dept, user_data in self.users.items():
            if token == user_data["token"]:
                return {
                    "sub": user_data["id"],
                    "department": user_data["department"],
                    "permissions": user_data["permissions"],
                }
        if token == mock_token_gestion():
            return {
                "sub": 2,
                "department": "gestion",
                "permissions": self.users["gestion"]["permissions"],
            }
        if token == mock_token_commercial():
            return {
                "sub": 1,
                "department": "commercial",
                "permissions": self.users["commercial"]["permissions"],
            }
        return None

    def reset_mocks(self):
        self.check_permission.reset_mock()
        self.verify_token.reset_mock()
        self.check_permission.return_value = None
        self.check_permission.side_effect = None


def mock_token_commercial():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImRlcGFydG1lbnQiOiJjb21tZXJjaWFsIiwicGVybWlzc2lvbnMiOlsicmVhZF9jb250cmFjdCJdfQ.1234567890"


def mock_token_gestion():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjIsImRlcGFydG1lbnQiOiJnZXN0aW9uIiwicGVybWlzc2lvbnMiOlsiY3JlYXRlX2NvbnRyYWN0IiwicmVhZF9jb250cmFjdCIsInVwZGF0ZV9jb250cmFjdCIsImRlbGV0ZV9jb250cmFjdCJdfQ.1234567890"


def mock_token_support():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjMsImRlcGFydG1lbnQiOiJzdXBwb3J0IiwicGVybWlzc2lvbnMiOlsicmVhZF9ldmVudCJdfQ.1234567890"
