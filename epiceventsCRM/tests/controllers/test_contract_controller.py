import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from epiceventsCRM.models.models import Contract, Client, User, Department
from epiceventsCRM.utils.auth import hash_password

@pytest.fixture
def test_data(db_session):
    """Créer les données de test dans la base de données."""
    # Départements
    commercial_dept = Department(departement_name="commercial")
    gestion_dept = Department(departement_name="gestion")
    support_dept = Department(departement_name="support")
    
    db_session.add_all([commercial_dept, gestion_dept, support_dept])
    db_session.commit()
    
    # Utilisateurs
    commercial_user = User(
        fullname="Commercial Test",
        email="commercial@test.com",
        password=hash_password("password"),
        departement_id=commercial_dept.id
    )
    
    gestion_user = User(
        fullname="Gestion Test",
        email="gestion@test.com",
        password=hash_password("password"),
        departement_id=gestion_dept.id
    )
    
    support_user = User(
        fullname="Support Test",
        email="support@test.com",
        password=hash_password("password"),
        departement_id=support_dept.id
    )
    
    db_session.add_all([commercial_user, gestion_user, support_user])
    db_session.commit()
    
    # Client
    client = Client(
        fullname="Client Test",
        email="client@test.com",
        phone_number=123456789,
        enterprise="Enterprise Test",
        create_date=datetime.now(),
        update_date=datetime.now(),
        sales_contact_id=commercial_user.id
    )
    
    db_session.add(client)
    db_session.commit()
    
    return {
        "commercial_user": commercial_user,
        "gestion_user": gestion_user,
        "support_user": support_user,
        "client": client,
        "commercial_dept": commercial_dept,
        "gestion_dept": gestion_dept,
        "support_dept": support_dept
    }

def test_contract_crud_simple(db_session, test_data):
    """Test simplifié des fonctionnalités CRUD pour un contrat."""
    # Créer un contrat directement dans la base de données
    contract = Contract(
        client_id=test_data["client"].id,
        amount=1000.0,
        remaining_amount=1000.0,
        create_date=datetime.now(),
        status=False,
        sales_contact_id=test_data["commercial_user"].id
    )
    
    db_session.add(contract)
    db_session.commit()
    
    # Récupérer le contrat via le DAO
    from epiceventsCRM.dao.contract_dao import ContractDAO
    contract_dao = ContractDAO()
    retrieved_contract = contract_dao.get(db_session, contract.id)
    
    # Vérifications
    assert retrieved_contract is not None
    assert retrieved_contract.id == contract.id
    assert retrieved_contract.amount == 1000.0
    
    # Test de mise à jour
    contract.amount = 1500.0
    contract.status = True
    db_session.commit()
    
    updated_contract = contract_dao.get(db_session, contract.id)
    assert updated_contract.amount == 1500.0
    assert updated_contract.status is True
    
    # Test de suppression
    db_session.delete(contract)
    db_session.commit()
    
    deleted_contract = contract_dao.get(db_session, contract.id)
    assert deleted_contract is None

def test_contract_departments_access(db_session, test_data):
    """Test des permissions par département sur les contrats."""
    # Créer un contrat
    contract = Contract(
        client_id=test_data["client"].id,
        amount=1000.0,
        remaining_amount=1000.0,
        create_date=datetime.now(),
        status=False,
        sales_contact_id=test_data["commercial_user"].id
    )
    
    db_session.add(contract)
    db_session.commit()
    
    # Test des permissions selon les départements
    from epiceventsCRM.utils.permissions import has_permission
    
    # 1. Le commercial ne peut pas créer des contrats
    assert has_permission(test_data["commercial_dept"].departement_name, "create_contract") is False
    
    # 2. Le département gestion peut créer des contrats
    assert has_permission(test_data["gestion_dept"].departement_name, "create_contract") is True
    
    # 3. Le support ne peut pas créer des contrats
    assert has_permission(test_data["support_dept"].departement_name, "create_contract") is False
    
    # 4. Le commercial peut mettre à jour ses contrats
    assert has_permission(test_data["commercial_dept"].departement_name, "update_contract") is True
    
    # 5. Le département gestion peut supprimer des contrats
    assert has_permission(test_data["gestion_dept"].departement_name, "delete_contract") is True
    
    # 6. Le commercial ne peut pas supprimer des contrats
    assert has_permission(test_data["commercial_dept"].departement_name, "delete_contract") is False
    
    # 7. Tous les départements peuvent lire des contrats
    assert has_permission(test_data["commercial_dept"].departement_name, "read_contract") is True
    assert has_permission(test_data["support_dept"].departement_name, "read_contract") is True
    assert has_permission(test_data["gestion_dept"].departement_name, "read_contract") is True 