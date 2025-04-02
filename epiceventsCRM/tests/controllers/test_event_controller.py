import pytest
from unittest.mock import MagicMock, patch, call
import jwt
from datetime import datetime, timedelta

from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.dao.event_dao import EventDAO
from epiceventsCRM.dao.contract_dao import ContractDAO
from epiceventsCRM.dao.client_dao import ClientDAO
from epiceventsCRM.dao.user_dao import UserDAO
from epiceventsCRM.models.models import Event, Contract, Client, User, Department

class TestEventController:
    """Tests pour la classe EventController"""

    def setup_method(self):
        """Configuration initiale avant chaque test"""
        self.session = MagicMock()
        self.event_dao = MagicMock(spec=EventDAO)
        self.contract_dao = MagicMock(spec=ContractDAO)
        self.client_dao = MagicMock(spec=ClientDAO)
        self.user_dao = MagicMock(spec=UserDAO)
        
        # Injection des mocks dans le contrôleur
        self.controller = EventController(self.session)
        self.controller.event_dao = self.event_dao
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
        
        self.event = Event(
            id=1,
            name="Test Event",
            contract_id=1,
            client_id=1,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Test Location",
            support_contact_id=1,
            attendees=10,
            notes="Test Notes",
            contract=self.contract,
            client=self.client,
            support_contact=self.support_user
        )
    
    def test_create_event_as_commercial(self):
        """Test de création d'un événement en tant que commercial"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        self.event_dao.create_event.return_value = self.event
        
        # Appel de la méthode à tester
        event_data = {
            "name": "Test Event",
            "contract_id": 1,
            "client_id": 1,
            "start_event": datetime.now(),
            "end_event": datetime.now() + timedelta(hours=2),
            "location": "Test Location",
            "attendees": 10,
            "notes": "Test Notes"
        }
        success, result = self.controller.create_event(
            token=self.token,
            event_data=event_data
        )
        
        # Vérifications
        assert success is True
        assert result == self.event
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
        self.event_dao.create_event.assert_called_once()
    
    def test_create_event_as_gestion(self):
        """Test de création d'un événement en tant que gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.contract_dao.get_contract_by_id.return_value = self.contract
        self.event_dao.create_event.return_value = self.event
        
        # Appel de la méthode à tester
        event_data = {
            "name": "Test Event",
            "contract_id": 1,
            "client_id": 1,
            "start_event": datetime.now(),
            "end_event": datetime.now() + timedelta(hours=2),
            "location": "Test Location",
            "attendees": 10,
            "notes": "Test Notes"
        }
        success, result = self.controller.create_event(
            token=self.token,
            event_data=event_data
        )
        
        # Vérifications
        assert success is True
        assert result == self.event
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(1)
        self.event_dao.create_event.assert_called_once()
    
    def test_create_event_as_support_denied(self):
        """Test de création d'un événement en tant que support (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        
        # Appel de la méthode à tester
        event_data = {
            "name": "Test Event",
            "contract_id": 1,
            "client_id": 1,
            "start_event": datetime.now(),
            "end_event": datetime.now() + timedelta(hours=2),
            "location": "Test Location",
            "attendees": 10,
            "notes": "Test Notes"
        }
        success, result = self.controller.create_event(
            token=self.token,
            event_data=event_data
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.create_event.assert_not_called()
    
    def test_create_event_contract_not_found(self):
        """Test de création d'un événement avec un contrat inexistant"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.contract_dao.get_contract_by_id.return_value = None
        
        # Appel de la méthode à tester
        event_data = {
            "name": "Test Event",
            "contract_id": 999,
            "client_id": 1,
            "start_event": datetime.now(),
            "end_event": datetime.now() + timedelta(hours=2),
            "location": "Test Location",
            "attendees": 10,
            "notes": "Test Notes"
        }
        success, result = self.controller.create_event(
            token=self.token,
            event_data=event_data
        )
        
        # Vérifications
        assert success is False
        assert "Contrat avec ID" in result
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.contract_dao.get_contract_by_id.assert_called_once_with(999)
        self.event_dao.create_event.assert_not_called()
    
    def test_get_event_as_commercial_owner(self):
        """Test d'accès à un événement par le commercial responsable"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.event_dao.get_event_by_id.return_value = self.event
        
        # Appel de la méthode à tester
        success, result = self.controller.get_event(
            token=self.token,
            event_id=1
        )
        
        # Vérifications
        assert success is True
        assert result == self.event
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_event_by_id.assert_called_once_with(1)
    
    def test_get_event_as_commercial_not_owner(self):
        """Test d'accès à un événement par un commercial non responsable"""
        # Créer un client avec un autre commercial
        other_commercial = User(
            id=4,
            fullname="Other Commercial",
            email="other@test.com",
            password="password",
            departement_id=1,
            department=self.commercial_department
        )
        other_client = Client(
            id=2,
            fullname="Other Client",
            email="other_client@test.com",
            phone_number=1234567890,
            enterprise="Other Enterprise",
            create_date=datetime.now(),
            update_date=datetime.now(),
            sales_contact_id=4
        )
        
        # Créer un contrat pour cet autre client
        other_contract = Contract(
            id=2,
            client_id=2,
            amount=2000.0,
            remaining_amount=2000.0,
            create_date=datetime.now(),
            status=False,
            sales_contact_id=4
        )
        
        # Créer un événement pour ce contrat
        other_event = Event(
            id=2,
            name="Other Event",
            contract_id=2,
            client_id=2,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Other Location",
            attendees=20,
            notes="Other Notes",
            support_contact_id=3,
            contract=other_contract,
            client=other_client
        )
        
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.event_dao.get_event_by_id.return_value = other_event
        self.client_dao.get_client_by_id.return_value = other_client
        
        # Appel de la méthode à tester
        success, result = self.controller.get_event(
            token=self.token,
            event_id=2
        )
        
        # Vérifications - Maintenant tous les collaborateurs peuvent lire tous les événements
        assert success is True
        assert result == other_event
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_event_by_id.assert_called_once_with(2)
    
    def test_get_event_as_gestion(self):
        """Test d'accès à un événement en tant que gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.event_dao.get_event_by_id.return_value = self.event
        
        # Appel de la méthode à tester
        success, result = self.controller.get_event(
            token=self.token,
            event_id=1
        )
        
        # Vérifications
        assert success is True
        assert result == self.event
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_event_by_id.assert_called_once_with(1)
    
    def test_get_event_as_support_with_access(self):
        """Test d'accès à un événement en tant que support avec accès"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.event_dao.get_event_by_id.return_value = self.event
        
        # Appel de la méthode à tester
        success, result = self.controller.get_event(
            token=self.token,
            event_id=1
        )
        
        # Vérifications
        assert success is True
        assert result == self.event
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_event_by_id.assert_called_once_with(1)
    
    def test_get_event_as_support_without_access(self):
        """Test d'accès à un événement en tant que support sans accès"""
        # Créer un autre support
        other_support = User(
            id=4,
            fullname="Other Support",
            email="other_support@test.com",
            password="password",
            departement_id=2,
            department=self.support_department
        )
        
        # Créer un événement avec l'autre support
        other_event = Event(
            id=2,
            name="Other Event",
            contract_id=1,
            client_id=1,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Other Location",
            support_contact_id=4,
            attendees=20,
            notes="Other Notes",
            contract=self.contract,
            client=self.client,
            support_contact=other_support
        )
        
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.event_dao.get_event_by_id.return_value = other_event
        
        # Appel de la méthode à tester
        success, result = self.controller.get_event(
            token=self.token,
            event_id=2
        )
        
        # Vérifications - Maintenant tous les événements sont accessibles
        assert success is True
        assert result == other_event
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_event_by_id.assert_called_once_with(2)
    
    def test_list_events_as_commercial(self):
        """Test de récupération des événements en tant que commercial"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.event_dao.get_all_events.return_value = [self.event]
        
        # Appel de la méthode à tester
        success, result = self.controller.list_events(
            token=self.token
        )
        
        # Vérifications
        assert success is True
        assert result == [self.event]
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_all_events.assert_called_once()
        self.client_dao.get_by_sales_contact.assert_not_called()
    
    def test_list_events_as_gestion(self):
        """Test de liste des événements en tant que gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.event_dao.get_all_events.return_value = [self.event]
        
        # Appel de la méthode à tester
        success, result = self.controller.list_events(self.token)
        
        # Vérifications
        assert success is True
        assert result == [self.event]
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_all_events.assert_called_once()
    
    def test_list_events_as_support(self):
        """Test de récupération des événements en tant que support"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.event_dao.get_all_events.return_value = [self.event]
        
        # Appel de la méthode à tester
        success, result = self.controller.list_events(
            token=self.token
        )
        
        # Vérifications
        assert success is True
        assert result == [self.event]
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_all_events.assert_called_once()
    
    def test_list_events_as_support_with_filter(self):
        """Test de récupération des événements filtrés en tant que support"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.event_dao.get_events_by_support_contact.return_value = [self.event]
        
        # Appel de la méthode à tester
        success, result = self.controller.list_events(
            token=self.token,
            filter_by_support=True
        )
        
        # Vérifications
        assert success is True
        assert result == [self.event]
        self.user_dao.get_user_by_id.assert_called_once_with(self.user_id)
        self.event_dao.get_events_by_support_contact.assert_called_once_with(self.user_id)
        self.event_dao.get_all_events.assert_not_called()
    
    def test_update_event_as_commercial_owner(self):
        """Test de mise à jour d'un événement par le commercial responsable (maintenant refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.event_dao.get_event_by_id.return_value = self.event
        
        # Appel de la méthode à tester
        update_data = {
            "name": "Updated Event",
            "location": "Updated Location",
            "attendees": 20,
            "notes": "Updated Notes"
        }
        
        success, result = self.controller.update_event(
            token=self.token,
            event_id=1,
            event_data=update_data
        )
        
        # Vérifications - Maintenant refusé pour les commerciaux
        assert success is False
        assert "Accès refusé" in result
        assert "les commerciaux ne peuvent pas modifier les événements" in result
        # get_user_by_id est appelé deux fois: une fois dans get_event et une fois dans update_event
        assert self.user_dao.get_user_by_id.call_count == 2
        self.event_dao.get_event_by_id.assert_called_once_with(1)
        self.event_dao.update_event.assert_not_called()
    
    def test_update_event_as_commercial_not_owner(self):
        """Test de mise à jour d'un événement par un commercial non responsable (également refusé)"""
        # Créer un autre commercial
        other_commercial = User(
            id=4,
            fullname="Other Commercial",
            email="other@test.com",
            password="password",
            departement_id=1,
            department=self.commercial_department
        )
        
        # Créer un autre client pour l'autre commercial
        other_client = Client(
            id=2,
            fullname="Other Client",
            email="other@test.com",
            phone_number=987654321,
            enterprise="Other Enterprise",
            create_date=datetime.now(),
            sales_contact_id=4,
            sales_contact=other_commercial
        )
        
        # Créer un autre contrat pour l'autre client
        other_contract = Contract(
            id=2,
            client_id=2,
            amount=2000.0,
            remaining_amount=2000.0,
            create_date=datetime.now(),
            status=False,
            sales_contact_id=4,
            client=other_client,
            sales_contact=other_commercial
        )
        
        # Créer un événement pour l'autre contrat
        other_event = Event(
            id=2,
            name="Other Event",
            contract_id=2,
            client_id=2,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Other Location",
            support_contact_id=3,
            attendees=20,
            notes="Other Notes",
            contract=other_contract,
            client=other_client,
            support_contact=self.support_user
        )
        
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.event_dao.get_event_by_id.return_value = other_event
        
        # Appel de la méthode à tester
        update_data = {
            "name": "Updated Event",
            "location": "Updated Location",
            "attendees": 20,
            "notes": "Updated Notes"
        }
        
        success, result = self.controller.update_event(
            token=self.token,
            event_id=2,
            event_data=update_data
        )
        
        # Vérifications - Tous les commerciaux sont refusés, qu'ils soient propriétaires ou non
        assert success is False
        assert "Accès refusé" in result
        assert "les commerciaux ne peuvent pas modifier les événements" in result
        # get_user_by_id est appelé deux fois: une fois dans get_event et une fois dans update_event
        assert self.user_dao.get_user_by_id.call_count == 2
        self.event_dao.get_event_by_id.assert_called_once_with(2)
        self.event_dao.update_event.assert_not_called()
    
    def test_update_event_as_gestion(self):
        """Test de mise à jour d'un événement en tant que gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.event_dao.get_event_by_id.return_value = self.event
        self.event_dao.update_event.return_value = self.event
        
        # Appel de la méthode à tester
        update_data = {
            "name": "Updated Event",
            "location": "Updated Location",
            "attendees": 20,
            "notes": "Updated Notes"
        }
        
        success, result = self.controller.update_event(
            token=self.token,
            event_id=1,
            event_data=update_data
        )
        
        # Vérifications
        assert success is True
        assert result == self.event
        self.user_dao.get_user_by_id.assert_has_calls([call(self.user_id)])
        self.event_dao.get_event_by_id.assert_called_once_with(1)
        self.event_dao.update_event.assert_called_once_with(1, update_data)
    
    def test_update_event_as_support(self):
        """Test de mise à jour d'un événement en tant que support"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.event_dao.get_event_by_id.return_value = self.event
        self.event_dao.update_event.return_value = self.event
        
        # Appel de la méthode à tester
        update_data = {
            "notes": "Updated Notes"
        }
        
        success, result = self.controller.update_event(
            token=self.token,
            event_id=1,
            event_data=update_data
        )
        
        # Vérifications
        assert success is True
        assert result == self.event
        self.user_dao.get_user_by_id.assert_has_calls([call(self.user_id)])
        self.event_dao.get_event_by_id.assert_called_once_with(1)
        self.event_dao.update_event.assert_called_once_with(1, update_data)
    
    def test_delete_event_as_gestion(self):
        """Test de suppression d'un événement en tant que gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.gestion_user
        self.event_dao.get_event_by_id.return_value = self.event
        self.event_dao.delete_event.return_value = True
        
        # Appel de la méthode à tester
        success, result = self.controller.delete_event(
            token=self.token,
            event_id=1
        )
        
        # Vérifications
        assert success is True
        assert result == "Événement supprimé avec succès"
        self.user_dao.get_user_by_id.assert_has_calls([call(self.user_id)])
        self.event_dao.get_event_by_id.assert_called_once_with(1)
        self.event_dao.delete_event.assert_called_once_with(1)
    
    def test_delete_event_as_commercial(self):
        """Test de suppression d'un événement en tant que commercial (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.event_dao.get_event_by_id.return_value = self.event
        
        # Appel de la méthode à tester
        success, result = self.controller.delete_event(
            token=self.token,
            event_id=1
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        assert "seul le département gestion" in result
        # get_user_by_id est appelé deux fois: une fois dans get_event et une fois dans delete_event
        assert self.user_dao.get_user_by_id.call_count == 2
        self.event_dao.delete_event.assert_not_called()
    
    def test_delete_event_as_support(self):
        """Test de suppression d'un événement en tant que support (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.event_dao.get_event_by_id.return_value = self.event
        
        # Appel de la méthode à tester
        success, result = self.controller.delete_event(
            token=self.token,
            event_id=1
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        # get_user_by_id est appelé deux fois: une fois dans get_event et une fois dans delete_event
        assert self.user_dao.get_user_by_id.call_count == 2
        self.event_dao.delete_event.assert_not_called()
    
    def test_assign_support_contact_as_gestion(self):
        """Test d'assignation d'un contact support en tant que gestion"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.side_effect = [
            self.gestion_user,  # Premier appel: l'utilisateur de gestion
            self.gestion_user,  # Deuxième appel: l'utilisateur de gestion (dans get_event)
            self.support_user   # Troisième appel: le contact support
        ]
        self.event_dao.get_event_by_id.return_value = self.event
        self.event_dao.assign_support_contact.return_value = self.event
        
        # Appel de la méthode à tester
        success, result = self.controller.assign_support_contact(
            token=self.token,
            event_id=1,
            support_contact_id=3
        )
        
        # Vérifications
        assert success is True
        assert result == self.event
        self.user_dao.get_user_by_id.assert_has_calls([
            call(self.user_id),
            call(self.user_id),
            call(3)
        ])
        self.event_dao.get_event_by_id.assert_called_once_with(1)
        self.event_dao.assign_support_contact.assert_called_once_with(1, 3)
    
    def test_assign_support_contact_as_commercial(self):
        """Test d'assignation d'un contact support en tant que commercial (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.commercial_user
        self.event_dao.get_event_by_id.return_value = self.event
        
        # Appel de la méthode à tester
        success, result = self.controller.assign_support_contact(
            token=self.token,
            event_id=1,
            support_contact_id=3
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        assert "seul le département gestion" in result
        # get_user_by_id est appelé deux fois: une fois dans get_event et une fois dans assign_support_contact
        assert self.user_dao.get_user_by_id.call_count == 2
        self.event_dao.assign_support_contact.assert_not_called()
    
    def test_assign_support_contact_as_support(self):
        """Test d'assignation d'un contact support en tant que support (refusé)"""
        # Configuration des mocks
        self.user_dao.get_user_by_id.return_value = self.support_user
        self.event_dao.get_event_by_id.return_value = self.event
        
        # Appel de la méthode à tester
        success, result = self.controller.assign_support_contact(
            token=self.token,
            event_id=1,
            support_contact_id=3
        )
        
        # Vérifications
        assert success is False
        assert "Accès refusé" in result
        # get_user_by_id est appelé deux fois: une fois dans get_event et une fois dans assign_support_contact
        assert self.user_dao.get_user_by_id.call_count == 2
        self.event_dao.assign_support_contact.assert_not_called() 