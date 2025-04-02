import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.models.models import Contract, Client, User, Department


class TestContractDAO:
    """Tests pour la classe ContractDAO"""

    def test_create_contract(self, db_session: Session):
        """Test de création d'un contrat"""
        # Créer des données de test (client et commercial)
        department = Department(departement_name="commercial")
        db_session.add(department)
        db_session.flush()

        sales_contact = User(
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()

        client = Client(
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()

        # Créer le contrat avec ContractDAO
        contract_dao = ContractDAO(db_session)
        contract = contract_dao.create_contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id,
            status=False
        )

        # Vérifier le contrat créé
        assert contract is not None
        assert contract.client_id == client.id
        assert contract.amount == 1000.0
        assert contract.remaining_amount == 1000.0
        assert contract.sales_contact_id == sales_contact.id
        assert contract.status is False
        assert contract.create_date is not None

    def test_get_contract_by_id(self, db_session: Session):
        """Test de récupération d'un contrat par ID"""
        # Créer un contrat de test
        contract_dao = ContractDAO(db_session)
        
        # Récupérer client et commercial existants ou les créer
        department = db_session.query(Department).filter_by(departement_name="commercial").first()
        if not department:
            department = Department(departement_name="commercial")
            db_session.add(department)
            db_session.flush()

        sales_contact = db_session.query(User).filter_by(email="commercial@test.com").first()
        if not sales_contact:
            sales_contact = User(
                fullname="Commercial Test",
                email="commercial@test.com",
                password="password",
                departement_id=department.id
            )
            db_session.add(sales_contact)
            db_session.flush()

        client = db_session.query(Client).filter_by(email="client@test.com").first()
        if not client:
            client = Client(
                fullname="Client Test",
                email="client@test.com",
                phone_number=123456789,
                enterprise="Enterprise Test",
                create_date=datetime.now(),
                sales_contact_id=sales_contact.id
            )
            db_session.add(client)
            db_session.flush()

        # Créer un contrat
        contract = contract_dao.create_contract(
            client_id=client.id,
            amount=1000.0,
            sales_contact_id=sales_contact.id
        )
        
        # Récupérer le contrat par ID
        retrieved_contract = contract_dao.get_contract_by_id(contract.id)
        
        # Vérifier le contrat récupéré
        assert retrieved_contract is not None
        assert retrieved_contract.id == contract.id
        assert retrieved_contract.client_id == client.id
        assert retrieved_contract.amount == 1000.0
        
        # Test avec un ID inexistant
        non_existent_contract = contract_dao.get_contract_by_id(9999)
        assert non_existent_contract is None
        
    def test_get_all_contracts(self, db_session: Session):
        """Test de récupération de tous les contrats"""
        # Récupérer le nombre de contrats existants
        contract_dao = ContractDAO(db_session)
        initial_count = len(contract_dao.get_all_contracts())
        
        # Créer client et commercial si nécessaire
        department = db_session.query(Department).filter_by(departement_name="commercial").first()
        if not department:
            department = Department(departement_name="commercial")
            db_session.add(department)
            db_session.flush()

        sales_contact = db_session.query(User).filter_by(email="commercial@test.com").first()
        if not sales_contact:
            sales_contact = User(
                fullname="Commercial Test",
                email="commercial@test.com",
                password="password",
                departement_id=department.id
            )
            db_session.add(sales_contact)
            db_session.flush()

        client = db_session.query(Client).filter_by(email="client@test.com").first()
        if not client:
            client = Client(
                fullname="Client Test",
                email="client@test.com",
                phone_number=123456789,
                enterprise="Enterprise Test",
                create_date=datetime.now(),
                sales_contact_id=sales_contact.id
            )
            db_session.add(client)
            db_session.flush()
            
        # Créer deux nouveaux contrats
        contract_dao.create_contract(
            client_id=client.id,
            amount=1500.0,
            sales_contact_id=sales_contact.id
        )
        
        contract_dao.create_contract(
            client_id=client.id,
            amount=2500.0,
            sales_contact_id=sales_contact.id
        )
        
        # Récupérer tous les contrats
        contracts = contract_dao.get_all_contracts()
        
        # Vérifier qu'il y a deux contrats de plus
        assert len(contracts) == initial_count + 2
        
    def test_get_contracts_by_client(self, db_session: Session):
        """Test de récupération des contrats par client"""
        contract_dao = ContractDAO(db_session)
        
        # Créer client et commercial si nécessaire
        department = db_session.query(Department).filter_by(departement_name="commercial").first()
        if not department:
            department = Department(departement_name="commercial")
            db_session.add(department)
            db_session.flush()

        sales_contact = db_session.query(User).filter_by(email="commercial@test.com").first()
        if not sales_contact:
            sales_contact = User(
                fullname="Commercial Test",
                email="commercial@test.com",
                password="password",
                departement_id=department.id
            )
            db_session.add(sales_contact)
            db_session.flush()

        # Créer un nouveau client pour ce test
        client = Client(
            fullname="Client Test 2",
            email="client2@test.com",
            phone_number=987654321,
            enterprise="Enterprise Test 2",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()
        
        # Créer deux contrats pour ce client
        contract_dao.create_contract(
            client_id=client.id,
            amount=3000.0,
            sales_contact_id=sales_contact.id
        )
        
        contract_dao.create_contract(
            client_id=client.id,
            amount=4000.0,
            sales_contact_id=sales_contact.id
        )
        
        # Récupérer les contrats par client
        client_contracts = contract_dao.get_contracts_by_client(client.id)
        
        # Vérifier qu'il y a deux contrats pour ce client
        assert len(client_contracts) == 2
        assert all(contract.client_id == client.id for contract in client_contracts)
        
    def test_get_contracts_by_sales_contact(self, db_session: Session):
        """Test de récupération des contrats par commercial"""
        contract_dao = ContractDAO(db_session)
        
        # Créer un nouveau commercial pour ce test
        department = db_session.query(Department).filter_by(departement_name="commercial").first()
        if not department:
            department = Department(departement_name="commercial")
            db_session.add(department)
            db_session.flush()

        sales_contact = User(
            fullname="Commercial Test 2",
            email="commercial2@test.com",
            password="password",
            departement_id=department.id
        )
        db_session.add(sales_contact)
        db_session.flush()
        
        # Créer un client
        client = Client(
            fullname="Client Test 3",
            email="client3@test.com",
            phone_number=555555555,
            enterprise="Enterprise Test 3",
            create_date=datetime.now(),
            sales_contact_id=sales_contact.id
        )
        db_session.add(client)
        db_session.flush()
        
        # Créer deux contrats pour ce commercial
        contract_dao.create_contract(
            client_id=client.id,
            amount=5000.0,
            sales_contact_id=sales_contact.id
        )
        
        contract_dao.create_contract(
            client_id=client.id,
            amount=6000.0,
            sales_contact_id=sales_contact.id
        )
        
        # Récupérer les contrats par commercial
        sales_contracts = contract_dao.get_contracts_by_sales_contact(sales_contact.id)
        
        # Vérifier qu'il y a deux contrats pour ce commercial
        assert len(sales_contracts) == 2
        assert all(contract.sales_contact_id == sales_contact.id for contract in sales_contracts)
        
    def test_update_contract(self, db_session: Session):
        """Test de mise à jour d'un contrat"""
        contract_dao = ContractDAO(db_session)
        
        # Récupérer client et commercial existants ou les créer
        department = db_session.query(Department).filter_by(departement_name="commercial").first()
        if not department:
            department = Department(departement_name="commercial")
            db_session.add(department)
            db_session.flush()

        sales_contact = db_session.query(User).filter_by(email="commercial@test.com").first()
        if not sales_contact:
            sales_contact = User(
                fullname="Commercial Test",
                email="commercial@test.com",
                password="password",
                departement_id=department.id
            )
            db_session.add(sales_contact)
            db_session.flush()

        client = db_session.query(Client).filter_by(email="client@test.com").first()
        if not client:
            client = Client(
                fullname="Client Test",
                email="client@test.com",
                phone_number=123456789,
                enterprise="Enterprise Test",
                create_date=datetime.now(),
                sales_contact_id=sales_contact.id
            )
            db_session.add(client)
            db_session.flush()
            
        # Créer un contrat
        contract = contract_dao.create_contract(
            client_id=client.id,
            amount=7000.0,
            sales_contact_id=sales_contact.id,
            status=False
        )
        
        # Mettre à jour le contrat
        update_data = {
            "amount": 8000.0,
            "status": True,
            "remaining_amount": 5000.0
        }
        updated_contract = contract_dao.update_contract(contract.id, update_data)
        
        # Vérifier le contrat mis à jour
        assert updated_contract is not None
        assert updated_contract.id == contract.id
        assert updated_contract.amount == 8000.0
        assert updated_contract.status is True
        assert updated_contract.remaining_amount == 5000.0
        
    def test_update_contract_status(self, db_session: Session):
        """Test de mise à jour du statut d'un contrat"""
        contract_dao = ContractDAO(db_session)
        
        # Récupérer client et commercial existants ou les créer
        department = db_session.query(Department).filter_by(departement_name="commercial").first()
        if not department:
            department = Department(departement_name="commercial")
            db_session.add(department)
            db_session.flush()

        sales_contact = db_session.query(User).filter_by(email="commercial@test.com").first()
        if not sales_contact:
            sales_contact = User(
                fullname="Commercial Test",
                email="commercial@test.com",
                password="password",
                departement_id=department.id
            )
            db_session.add(sales_contact)
            db_session.flush()

        client = db_session.query(Client).filter_by(email="client@test.com").first()
        if not client:
            client = Client(
                fullname="Client Test",
                email="client@test.com",
                phone_number=123456789,
                enterprise="Enterprise Test",
                create_date=datetime.now(),
                sales_contact_id=sales_contact.id
            )
            db_session.add(client)
            db_session.flush()
            
        # Créer un contrat non signé
        contract = contract_dao.create_contract(
            client_id=client.id,
            amount=9000.0,
            sales_contact_id=sales_contact.id,
            status=False
        )
        
        # Mettre à jour le statut à signé
        updated_contract = contract_dao.update_contract_status(contract.id, True)
        
        # Vérifier le statut mis à jour
        assert updated_contract is not None
        assert updated_contract.status is True
        
        # Mettre à jour le statut à non signé
        updated_contract = contract_dao.update_contract_status(contract.id, False)
        
        # Vérifier le statut mis à jour
        assert updated_contract is not None
        assert updated_contract.status is False
        
    def test_update_remaining_amount(self, db_session: Session):
        """Test de mise à jour du montant restant d'un contrat"""
        contract_dao = ContractDAO(db_session)
        
        # Récupérer client et commercial existants ou les créer
        department = db_session.query(Department).filter_by(departement_name="commercial").first()
        if not department:
            department = Department(departement_name="commercial")
            db_session.add(department)
            db_session.flush()

        sales_contact = db_session.query(User).filter_by(email="commercial@test.com").first()
        if not sales_contact:
            sales_contact = User(
                fullname="Commercial Test",
                email="commercial@test.com",
                password="password",
                departement_id=department.id
            )
            db_session.add(sales_contact)
            db_session.flush()

        client = db_session.query(Client).filter_by(email="client@test.com").first()
        if not client:
            client = Client(
                fullname="Client Test",
                email="client@test.com",
                phone_number=123456789,
                enterprise="Enterprise Test",
                create_date=datetime.now(),
                sales_contact_id=sales_contact.id
            )
            db_session.add(client)
            db_session.flush()
            
        # Créer un contrat avec un montant initial
        contract = contract_dao.create_contract(
            client_id=client.id,
            amount=10000.0,
            sales_contact_id=sales_contact.id
        )
        
        # Vérifier que le montant restant est égal au montant initial
        assert contract.remaining_amount == 10000.0
        
        # Mettre à jour le montant restant
        updated_contract = contract_dao.update_remaining_amount(contract.id, 7500.0)
        
        # Vérifier le montant restant mis à jour
        assert updated_contract is not None
        assert updated_contract.remaining_amount == 7500.0
        
    def test_delete_contract(self, db_session: Session):
        """Test de suppression d'un contrat"""
        contract_dao = ContractDAO(db_session)
        
        # Récupérer client et commercial existants ou les créer
        department = db_session.query(Department).filter_by(departement_name="commercial").first()
        if not department:
            department = Department(departement_name="commercial")
            db_session.add(department)
            db_session.flush()

        sales_contact = db_session.query(User).filter_by(email="commercial@test.com").first()
        if not sales_contact:
            sales_contact = User(
                fullname="Commercial Test",
                email="commercial@test.com",
                password="password",
                departement_id=department.id
            )
            db_session.add(sales_contact)
            db_session.flush()

        client = db_session.query(Client).filter_by(email="client@test.com").first()
        if not client:
            client = Client(
                fullname="Client Test",
                email="client@test.com",
                phone_number=123456789,
                enterprise="Enterprise Test",
                create_date=datetime.now(),
                sales_contact_id=sales_contact.id
            )
            db_session.add(client)
            db_session.flush()
            
        # Créer un contrat à supprimer
        contract = contract_dao.create_contract(
            client_id=client.id,
            amount=11000.0,
            sales_contact_id=sales_contact.id
        )
        
        # Vérifier que le contrat existe
        assert contract_dao.get_contract_by_id(contract.id) is not None
        
        # Supprimer le contrat
        success = contract_dao.delete_contract(contract.id)
        
        # Vérifier que la suppression a réussi
        assert success is True
        
        # Vérifier que le contrat n'existe plus
        assert contract_dao.get_contract_by_id(contract.id) is None
        
        # Tester la suppression d'un contrat inexistant
        success = contract_dao.delete_contract(9999)
        assert success is False 