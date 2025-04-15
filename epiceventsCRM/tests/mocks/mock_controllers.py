from typing import Dict, Optional
from datetime import datetime, timezone

class MockAuthController:
    """Mock du contrôleur d'authentification avec des utilisateurs spécifiques à chaque département"""
    
    def __init__(self, department=None):
        self.users = {
            "commercial": {
                "id": 1,
                "department": "commercial",
                "permissions": ["create_client", "read_client", "update_client", "create_event", "read_event"]
            },
            "gestion": {
                "id": 2,
                "department": "gestion",
                "permissions": ["create_contract", "read_contract", "update_contract", "delete_contract"]
            },
            "support": {
                "id": 3,
                "department": "support",
                "permissions": ["create_event", "read_event", "update_event"]
            }
        }
        self.current_user = self.users.get(department) if department else None

    def check_permission(self, token, permission):
        if not self.current_user:
            return False
        if token == "invalid_token":
            return False
        return permission in self.current_user["permissions"]

    def verify_token(self, token):
        if not self.current_user or token == "invalid_token":
            return None
        return {
            "sub": self.current_user["id"],
            "department": self.current_user["department"],
            "permissions": self.current_user["permissions"]
        }

    def decode_token(self, token):
        if not self.current_user or token == "invalid_token":
            return None
        return {
            "sub": self.current_user["id"],
            "department": self.current_user["department"]
        } 