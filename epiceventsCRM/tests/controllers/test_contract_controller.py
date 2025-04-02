import pytest
from unittest.mock import MagicMock, patch, call
import jwt
from datetime import datetime

from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Contract, Client, User, Department

class TestContractController:
    """Tests pour la classe ContractController"""

    def setup_method(self):
        """Configuration initiale avant chaque test"""
        self.session = MagicMock()
        self.contract_dao = MagicMock(spec=ContractDAO)
        self.client_dao = MagicMock(spec=ClientDAO)
        self.user_dao = MagicMock(spec=UserDAO)
        
        # Injection des mocks dans le contrôleur
        self.controller = ContractController(self.session)
        self.controller.contract_dao = self.contract_dao
        self.controller.client_dao = self.client_dao
        self.controller.user_dao = self.user_dao
        
        # Créer un token de test
        self.user_id = 1
        self.token = jwt.encode({"user_id": self.user_id}, "secret_key")
        
        # Créer des objets de test
        self.commercial_department = Department(id=1, departement_name="commercial")
        self.gestion_department = Department(id=3, departement_name="gestion")
        self.support_department = Department(id=2, departement_name="support")
        
        self.commercial_user = User(
            id=1,
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=1,
            department=self.commercial_department
        )
        
        self.gestion_user = User(
            id=2,
            fullname="Gestion Test",
            email="gestion@test.com",
            password="password",
            departement_id=3,
            department=self.gestion_department
        )
        
        self.support_user = User(
            id=3,
            fullname="Support Test",
            email="support@test.com",
            password="password",
            departement_id=2,
            department=self.support_department
        )
        
        self.client = Client(
            id=1,
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=1,
            sales_contact=self.commercial_user
        )
        
        self.contract = Contract(
            id=1,
            client_id=1,
            amount=1000.0,
            remaining_amount=1000.0,
            create_date=datetime.now(),
            status=False,
            sales_contact_id=1,
            client=self.client,
            sales_contact=self.commercial_user
        )
    
    def test_create_contract_as_commercial(self):
        """Test de création d'un contrat en tant que commercial (maintenant refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        
        # Appel de la méthode à tester
        success, result = self.controller.create_contract(
            token=self.token,
            client_id=1,
            amount=1000.0
        )
        
        # Vérifications - Maintenant refusé pour les commerciaux
        assert success is False
        assert "Accès refusé" in result
        assert "seul le département gestion" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.client_dao.get_client_by_id.assert_not_called()
        self.contract_dao.create_contract.assert_not_called()
    
    def test_create_contract_as_gestion(self):
        """Test de création d'un contrat en tant que gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.side_effect = [
            self.gestion_user,  # Premier appel: utilisateur de gestion
            self.commercial_user  # Deuxième appel: commercial du client (sales_contact_id=1)
        ]
        self.client_dao.get_client_by_id.return_value = self.client
        self.contract_dao.create_contract.return_value = self.contract
        
        # Appel de la méthode à tester
        success, result = self.controller.create_contract(
            token=self.token,
            client_id=1,
            amount=1000.0
        )
        
        # Vérifications
        assert success is True
        assert result == self.contract
        # On vérifie que get_user_by_id est appelé deux fois
        assert self.user_dao.get_user_by_id.call_count == 2
        self.user_dao.get_user_by_id.assert_has_calls([call(self.user_id), call(1)])
        self.client_dao.get_client_by_id.assert_called_once_with(1)
        # La gestion devrait utiliser le commercial du client
        self.contract_dao.create_contract.assert_called_once_with(
            client_id=1,
            amount=1000.0,
            sales_contact_id=1  # ID du commercial du client
        )
    
    def test_create_contract_as_support_denied(self):
        """Test de création d'un contrat en tant que support (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        
        # Appel de la méthode à tester
        success, result = self.controller.create_contract(
            token=self.token,
            client_id=1,
            amount=1000.0
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.create_contract.assert_not_called()
    
    def test_create_contract_with_explicit_sales_contact(self):
        """Test de création d'un contrat avec un commercial spécifié (maintenant refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        
        # Appel de la méthode à tester
        success, result = self.controller.create_contract(
            token=self.token,
            client_id=1,
            amount=1000.0,
            sales_contact_id=1  # Commercial spécifié explicitement
        )
        
        # Vérifications - Maintenant refusé pour les commerciaux
        assert success is False
        assert "Accès refusé" in result
        assert "seul le département gestion" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.client_dao.get_client_by_id.assert_not_called()
        self.contract_dao.create_contract.assert_not_called()
    
    def test_create_contract_client_not_found(self):
        """Test de création d'un contrat avec un client inexistant"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.client_dao.get_client_by_id.return_value = None
        
        # Appel de la méthode à tester
        success, result = self.controller.create_contract(
            token=self.token,
            client_id=999,
            amount=1000.0
        )
        
        # Vérifications
        assert success is False
        assert "Client avec ID" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.client_dao.get_client_by_id.assert_called_once_with(999)
        self.contract_dao.create_contract.assert_not_called()
    
    def test_get_contract_as_commercial_owner(self):
        """Test d'accès à un contrat par le commercial responsable"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        
        # Appel de la méthode à tester
        success, result = self.controller.get_contract(
            token=self.token,
            contract_id=1
        )
        
        # Vérifications
        assert success is True
        assert result == self.contract
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
    
    def test_get_contract_as_commercial_not_owner(self):
        """Test d'accès à un contrat par un commercial non responsable"""
        # Créer un autre commercial
        other_commercial = User(
            id=4,
            fullname="Other Commercial",
            email="other@test.com",
            password="password",
            departement_id=1,
            department=self.commercial_department
        )
        
        # Configurez le contrat pour qu'il appartienne à l'autre commercial
        contract = Contract(
            id=1,
            client_id=1,
            amount=1000.0,
            remaining_amount=1000.0,
            create_date=datetime.now(),
            status=False,
            sales_contact_id=4,  # Autre commercial
            client=self.client,
            sales_contact=other_commercial
        )
        
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.contract_dao.get_contract_by_id.return_value = contract
        
        # Appel de la méthode à tester
        success, result = self.controller.get_contract(
            token=self.token,
            contract_id=1
        )
        
        # Vérifications - Maintenant tous les collaborateurs peuvent lire tous les contrats
        assert success is True
        assert result == contract
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
    
    def test_get_contract_as_gestion(self):
        """Test d'accès à un contrat par la gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        
        # Appel de la méthode à tester
        success, result = self.controller.get_contract(
            token=self.token,
            contract_id=1
        )
        
        # Vérifications
        assert success is True
        assert result == self.contract
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
    
    def test_get_contract_as_support_with_access(self):
        """Test d'accès à un contrat par le support avec un événement lié"""
        # Créer un événement lié au contrat et au commercial
        event = MagicMock()
        event.contract_id = 1
        self.support_user.events = [event]
        
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        
        # Appel de la méthode à tester
        success, result = self.controller.get_contract(
            token=self.token,
            contract_id=1
        )
        
        # Vérifications
        assert success is True
        assert result == self.contract
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
    
    def test_get_contract_as_support_without_access(self):
        """Test d'accès à un contrat par le support sans événement lié"""
        # Support sans événement lié à ce contrat
        self.support_user.events = []
        
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        
        # Appel de la méthode à tester
        success, result = self.controller.get_contract(
            token=self.token,
            contract_id=1
        )
        
        # Vérifications - Maintenant tous les collaborateurs peuvent lire tous les contrats
        assert success is True
        assert result == self.contract
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
    
    def test_list_contracts_as_commercial(self):
        """Test de récupération des contrats en tant que commercial"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.contract_dao.get_all_contracts.return_value = [self.contract]
        
        # Appel de la méthode à tester
        success, result = self.controller.list_contracts(
            token=self.token
        )
        
        # Vérifications - Tous les collaborateurs peuvent voir tous les contrats
        assert success is True
        assert result == [self.contract]
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_all_contracts.assert_called_once()
        self.contract_dao.get_contracts_by_sales_contact.assert_not_called()
    
    def test_list_contracts_as_gestion(self):
        """Test de récupération des contrats en tant que gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.contract_dao.get_all_contracts.return_value = [self.contract]
        
        # Appel de la méthode à tester
        success, result = self.controller.list_contracts(
            token=self.token
        )
        
        # Vérifications
        assert success is True
        assert result == [self.contract]
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_all_contracts.assert_called_once()
        self.contract_dao.get_contracts_by_sales_contact.assert_not_called()
    
    def test_list_contracts_as_support(self):
        """Test de récupération des contrats en tant que support"""
        # Créer un événement lié au contrat
        event = MagicMock()
        event.contract_id = 1
        self.support_user.events = [event]
        
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.contract_dao.get_all_contracts.return_value = [self.contract]
        
        # Appel de la méthode à tester
        success, result = self.controller.list_contracts(
            token=self.token
        )
        
        # Vérifications
        assert success is True
        assert result == [self.contract]
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_all_contracts.assert_called_once()
    
    def test_update_contract_as_commercial_owner(self):
        """Test de mise à jour d'un contrat par le commercial responsable"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        self.client_dao.get_client_by_id.return_value = self.client  # Le client du commercial
        
        updated_contract = Contract(
            id=1,
            client_id=1,
            amount=2000.0,  # Montant mis à jour
            remaining_amount=2000.0,
            create_date=datetime.now(),
            status=True,  # Statut mis à jour
            sales_contact_id=1,
            client=self.client,
            sales_contact=self.commercial_user
        )
        self.contract_dao.update_contract.return_value = updated_contract
        
        # Données de mise à jour
        update_data = {
            "amount": 2000.0,
            "status": True
        }
        
        # Appel de la méthode à tester
        success, result = self.controller.update_contract(
            token=self.token,
            contract_id=1,
            update_data=update_data
        )
        
        # Vérifications
        assert success is True
        assert result == updated_contract
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
        self.client_dao.get_client_by_id.assert_called_once_with(1)  # Vérifie que le client a été récupéré
        self.contract_dao.update_contract.assert_called_once_with(1, update_data)
    
    def test_update_contract_as_commercial_not_owner(self):
        """Test de mise à jour d'un contrat par un commercial non responsable"""
        # Créer un autre commercial
        other_commercial = User(
            id=4,
            fullname="Other Commercial",
            email="other@test.com",
            password="password",
            departement_id=1,
            department=self.commercial_department
        )
        
        # Configurer le contrat pour qu'il appartienne à l'autre commercial
        contract = Contract(
            id=1,
            client_id=1,
            amount=1000.0,
            remaining_amount=1000.0,
            create_date=datetime.now(),
            status=False,
            sales_contact_id=4,  # Autre commercial
            client=self.client,
            sales_contact=other_commercial
        )
        
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.contract_dao.get_contract_by_id.return_value = contract
        
        # Données de mise à jour
        update_data = {
            "amount": 2000.0,
            "status": True
        }
        
        # Appel de la méthode à tester
        success, result = self.controller.update_contract(
            token=self.token,
            contract_id=1,
            update_data=update_data
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
        self.contract_dao.update_contract.assert_not_called()
    
    def test_update_contract_as_gestion(self):
        """Test de mise à jour d'un contrat par la gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        
        updated_contract = Contract(
            id=1,
            client_id=1,
            amount=2000.0,  # Montant mis à jour
            remaining_amount=2000.0,
            create_date=datetime.now(),
            status=True,  # Statut mis à jour
            sales_contact_id=1,
            client=self.client,
            sales_contact=self.commercial_user
        )
        self.contract_dao.update_contract.return_value = updated_contract
        
        # Données de mise à jour
        update_data = {
            "amount": 2000.0,
            "status": True
        }
        
        # Appel de la méthode à tester
        success, result = self.controller.update_contract(
            token=self.token,
            contract_id=1,
            update_data=update_data
        )
        
        # Vérifications
        assert success is True
        assert result == updated_contract
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
        self.contract_dao.update_contract.assert_called_once_with(1, update_data)
    
    def test_update_contract_as_support(self):
        """Test de mise à jour d'un contrat par le support (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        
        # Données de mise à jour
        update_data = {
            "amount": 2000.0,
            "status": True
        }
        
        # Appel de la méthode à tester
        success, result = self.controller.update_contract(
            token=self.token,
            contract_id=1,
            update_data=update_data
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
        self.contract_dao.update_contract.assert_not_called()
    
    def test_delete_contract_as_gestion(self):
        """Test de suppression d'un contrat par la gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        self.contract_dao.delete_contract.return_value = True
        
        # Appel de la méthode à tester
        success, result = self.controller.delete_contract(
            token=self.token,
            contract_id=1
        )
        
        # Vérifications
        assert success is True
        assert "supprimé avec succès" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
        self.contract_dao.delete_contract.assert_called_once_with(1)
    
    def test_delete_contract_as_commercial(self):
        """Test de suppression d'un contrat par un commercial (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        
        # Appel de la méthode à tester
        success, result = self.controller.delete_contract(
            token=self.token,
            contract_id=1
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_not_called()
        self.contract_dao.delete_contract.assert_not_called()
    
    def test_delete_contract_as_support(self):
        """Test de suppression d'un contrat par le support (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        
        # Appel de la méthode à tester
        success, result = self.controller.delete_contract(
            token=self.token,
            contract_id=1
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_not_called()
        self.contract_dao.delete_contract.assert_not_called()
    
    def test_create_contract_as_commercial_denied(self):
        """Test de création d'un contrat en tant que commercial (maintenant refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.client_dao.get_client_by_id.return_value = self.client
        self.user_dao.get_user_by_id.return_value = self.commercial_user  # Pour la vérification du commercial
        
        # Appel de la méthode à tester
        success, result = self.controller.create_contract(
            token=self.token,
            client_id=1,
            amount=1000.0,
            sales_contact_id=self.user_id
        )
        
        # Vérifications - Désormais refusé pour les commerciaux
        assert success is False
        assert "Accès refusé" in result
        self.user_dao.get_user_by_id.assert_called_with(self.user_id)
        self.client_dao.get_client_by_id.assert_not_called()
        self.contract_dao.create_contract.assert_not_called() 