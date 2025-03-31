import pytest
from epiceventsCRM.models.models import Department as ModelDepartment
from epiceventsCRM.utils.permissions import Department, get_department_permissions, has_permission

def test_department_permissions():
    """Test les permissions par département."""
    # Test des permissions commercial
    assert has_permission(Department("commercial"), "create_client")
    assert has_permission(Department("commercial"), "read_client")
    assert has_permission(Department("commercial"), "update_client")
    assert has_permission(Department("commercial"), "delete_client")
    assert has_permission(Department("commercial"), "create_contract")
    assert has_permission(Department("commercial"), "read_contract")
    assert has_permission(Department("commercial"), "update_contract")
    assert not has_permission(Department("commercial"), "delete_contract")
    assert not has_permission(Department("commercial"), "create_event")
    assert not has_permission(Department("commercial"), "read_event")
    assert not has_permission(Department("commercial"), "update_event")
    assert not has_permission(Department("commercial"), "delete_event")

    # Test des permissions support
    assert not has_permission(Department("support"), "create_client")
    assert has_permission(Department("support"), "read_client")
    assert not has_permission(Department("support"), "update_client")
    assert not has_permission(Department("support"), "delete_client")
    assert not has_permission(Department("support"), "create_contract")
    assert has_permission(Department("support"), "read_contract")
    assert not has_permission(Department("support"), "update_contract")
    assert not has_permission(Department("support"), "delete_contract")
    assert has_permission(Department("support"), "create_event")
    assert has_permission(Department("support"), "read_event")
    assert has_permission(Department("support"), "update_event")
    assert not has_permission(Department("support"), "delete_event")

    # Test des permissions gestion
    assert not has_permission(Department("gestion"), "create_client")
    assert not has_permission(Department("gestion"), "read_client")
    assert not has_permission(Department("gestion"), "update_client")
    assert not has_permission(Department("gestion"), "delete_client")
    assert has_permission(Department("gestion"), "create_contract")
    assert has_permission(Department("gestion"), "read_contract")
    assert has_permission(Department("gestion"), "update_contract")
    assert not has_permission(Department("gestion"), "delete_contract")
    assert not has_permission(Department("gestion"), "create_event")
    assert has_permission(Department("gestion"), "read_event")
    assert has_permission(Department("gestion"), "update_event")
    assert not has_permission(Department("gestion"), "delete_event")
    
    # Test des permissions de gestion des utilisateurs
    assert has_permission(Department("gestion"), "create_user")
    assert has_permission(Department("gestion"), "read_user")
    assert has_permission(Department("gestion"), "update_user")
    assert has_permission(Department("gestion"), "delete_user")
    assert not has_permission(Department("commercial"), "create_user")
    assert not has_permission(Department("commercial"), "read_user")
    assert not has_permission(Department("commercial"), "update_user")
    assert not has_permission(Department("commercial"), "delete_user")
    assert not has_permission(Department("support"), "create_user")
    assert not has_permission(Department("support"), "read_user")
    assert not has_permission(Department("support"), "update_user")
    assert not has_permission(Department("support"), "delete_user")

def test_get_department_permissions():
    """Test la récupération des permissions par département."""
    # Test des permissions commercial
    commercial_perms = get_department_permissions(Department("commercial"))
    assert "create_client" in commercial_perms
    assert "read_client" in commercial_perms
    assert "update_client" in commercial_perms
    assert "delete_client" in commercial_perms
    assert "create_contract" in commercial_perms
    assert "read_contract" in commercial_perms
    assert "update_contract" in commercial_perms
    assert "delete_contract" not in commercial_perms
    assert "create_event" not in commercial_perms
    assert "read_event" not in commercial_perms
    assert "update_event" not in commercial_perms
    assert "delete_event" not in commercial_perms

    # Test des permissions support
    support_perms = get_department_permissions(Department("support"))
    assert "create_client" not in support_perms
    assert "read_client" in support_perms
    assert "update_client" not in support_perms
    assert "delete_client" not in support_perms
    assert "create_contract" not in support_perms
    assert "read_contract" in support_perms
    assert "update_contract" not in support_perms
    assert "delete_contract" not in support_perms
    assert "create_event" in support_perms
    assert "read_event" in support_perms
    assert "update_event" in support_perms
    assert "delete_event" not in support_perms

    # Test des permissions gestion
    gestion_perms = get_department_permissions(Department("gestion"))
    assert "create_client" not in gestion_perms
    assert "read_client" not in gestion_perms
    assert "update_client" not in gestion_perms
    assert "delete_client" not in gestion_perms
    assert "create_contract" in gestion_perms
    assert "read_contract" in gestion_perms
    assert "update_contract" in gestion_perms
    assert "delete_contract" not in gestion_perms
    assert "create_event" not in gestion_perms
    assert "read_event" in gestion_perms
    assert "update_event" in gestion_perms
    assert "delete_event" not in gestion_perms
    assert "create_user" in gestion_perms
    assert "read_user" in gestion_perms
    assert "update_user" in gestion_perms
    assert "delete_user" in gestion_perms

def test_invalid_department():
    """Test avec un département invalide."""
    # Test avec une chaîne invalide
    assert list(get_department_permissions("INVALID_DEPARTMENT")) == []
    assert not has_permission("INVALID_DEPARTMENT", "create_client")
    assert not has_permission("INVALID_DEPARTMENT", "read_client")
    assert not has_permission("INVALID_DEPARTMENT", "update_client")
    assert not has_permission("INVALID_DEPARTMENT", "delete_client")
    assert not has_permission("INVALID_DEPARTMENT", "create_contract")
    assert not has_permission("INVALID_DEPARTMENT", "read_contract")
    assert not has_permission("INVALID_DEPARTMENT", "update_contract")
    assert not has_permission("INVALID_DEPARTMENT", "delete_contract")
    assert not has_permission("INVALID_DEPARTMENT", "create_event")
    assert not has_permission("INVALID_DEPARTMENT", "read_event")
    assert not has_permission("INVALID_DEPARTMENT", "update_event")
    assert not has_permission("INVALID_DEPARTMENT", "delete_event") 