import pytest
from unittest.mock import MagicMock, patch, call
import click
from click.testing import CliRunner
from datetime import datetime, timedelta

from epiceventsCRM.views.event_view import EventView
from epiceventsCRM.controllers.event_controller import EventController
from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.models.models import Event, Contract, Client, User, Department


class TestEventView:
    """Tests pour la classe EventView"""

    def setup_method(self):
        """Configuration initiale avant chaque test"""
        self.session = MagicMock()
        self.token = "fake_token"
        self.event_controller = MagicMock(spec=EventController)
        self.contract_controller = MagicMock(spec=ContractController)
        self.client_controller = MagicMock(spec=ClientController)
        
        # Création de l'objet à tester
        self.view = EventView(self.session, self.token)
        self.view.event_controller = self.event_controller
        self.view.contract_controller = self.contract_controller
        self.view.client_controller = self.client_controller
        
        # Création d'objets de test
        self.commercial_department = Department(id=1, departement_name="commercial")
        self.support_department = Department(id=2, departement_name="support")
        
        self.commercial_user = User(
            id=1,
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=1,
            department=self.commercial_department
        )
        
        self.support_user = User(
            id=2,
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
            support_contact_id=2,
            attendees=10,
            notes="Test Notes",
            contract=self.contract,
            client=self.client,
            support_contact=self.support_user
        )
        
        self.updated_event = Event(
            id=1,
            name="Updated Event",
            contract_id=1,
            client_id=1,
            start_event=datetime.now(),
            end_event=datetime.now() + timedelta(hours=2),
            location="Updated Location",
            support_contact_id=2,
            attendees=20,
            notes="Updated Notes",
            contract=self.contract,
            client=self.client,
            support_contact=self.support_user
        )
        
        # Créer un mock pour click.echo pour ne pas polluer la sortie des tests
        self.echo_patch = patch('epiceventsCRM.views.event_view.click.echo')
        self.mock_echo = self.echo_patch.start()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        self.echo_patch.stop()
    
    def test_display_event(self):
        """Test d'affichage des détails d'un événement"""
        # Appel de la méthode à tester
        self.view.display_event(self.event)
        
        # Vérifier que click.echo a été appelé avec les bonnes informations
        assert self.mock_echo.call_count >= 8  # Au moins 8 appels pour afficher les détails
        
        # Vérifier que les informations importantes sont affichées
        call_args_list = [call[0][0] for call in self.mock_echo.call_args_list]
        assert any(f"ID: {self.event.id}" in str(arg) for arg in call_args_list)
        assert any(f"Nom: {self.event.name}" in str(arg) for arg in call_args_list)
        assert any(f"Contrat ID: {self.event.contract_id}" in str(arg) for arg in call_args_list)
        assert any(f"Client ID: {self.event.client_id}" in str(arg) for arg in call_args_list)
        assert any(f"Lieu: {self.event.location}" in str(arg) for arg in call_args_list)
        assert any(f"Contact support ID: {self.event.support_contact_id}" in str(arg) for arg in call_args_list)
        assert any(f"Nombre de participants: {self.event.attendees}" in str(arg) for arg in call_args_list)
        assert any(f"Notes: {self.event.notes}" in str(arg) for arg in call_args_list)
    
    def test_list_events_success(self):
        """Test de listage des événements (succès)"""
        # Configuration des mocks
        self.event_controller.list_events.return_value = (True, [self.event])
        
        # Appel de la méthode à tester
        self.view.list_events()
        
        # Vérifications
        self.event_controller.list_events.assert_called_once_with(self.token, False)
        self.mock_echo.assert_has_calls([
            call(f"Liste des événements (1 trouvés):")
        ])
    
    def test_list_events_empty(self):
        """Test de listage des événements (aucun événement)"""
        # Configuration des mocks
        self.event_controller.list_events.return_value = (True, [])
        
        # Appel de la méthode à tester
        self.view.list_events()
        
        # Vérifications
        self.event_controller.list_events.assert_called_once_with(self.token, False)
        self.mock_echo.assert_called_once_with("Aucun événement trouvé.")
    
    def test_list_events_error(self):
        """Test de listage des événements (erreur)"""
        # Configuration des mocks
        self.event_controller.list_events.return_value = (False, "Erreur d'accès")
        
        # Appel de la méthode à tester
        self.view.list_events()
        
        # Vérifications
        self.event_controller.list_events.assert_called_once_with(self.token, False)
        self.mock_echo.assert_called_once_with("Erreur: Erreur d'accès")
    
    def test_get_event_by_id_success(self):
        """Test de récupération d'un événement par ID (succès)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (True, self.event)
        
        # Appel de la méthode à tester
        self.view.get_event_by_id(1)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 1)
        
        # Vérifier que click.echo a été appelé pour afficher les détails
        assert self.mock_echo.call_count > 0
        
        # Vérifier l'affichage du titre
        call_args_list = [call[0][0] for call in self.mock_echo.call_args_list]
        assert any("Détails de l'événement" in str(arg) for arg in call_args_list)
    
    def test_get_event_by_id_error(self):
        """Test de récupération d'un événement par ID (erreur)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (False, "Événement non trouvé")
        
        # Appel de la méthode à tester
        self.view.get_event_by_id(999)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 999)
        
        # Vérifier que click.echo a été appelé pour afficher l'erreur
        self.mock_echo.assert_any_call("Erreur: Événement non trouvé")
    
    @patch('epiceventsCRM.views.event_view.click.prompt')
    @patch('epiceventsCRM.views.event_view.click.confirm')
    def test_create_event_success(self, mock_confirm, mock_prompt):
        """Test de création d'un événement (succès)"""
        # Configuration des mocks
        self.contract_controller.list_contracts.return_value = (True, [self.contract])
        mock_prompt.side_effect = [
            1,  # contract_index
            "Test Event",  # name
            "Test Location",  # location
            10,  # attendees
            "Test Notes"  # notes
        ]
        
        mock_confirm.return_value = False  # Pas de contact support spécifique
        self.event_controller.create_event.return_value = (True, self.event)
        
        # Appel de la méthode à tester
        self.view.create_event()
        
        # Vérifications
        self.contract_controller.list_contracts.assert_called_once_with(self.token)
        assert mock_prompt.call_count == 5
        self.event_controller.create_event.assert_called_once()
        call_args = self.event_controller.create_event.call_args[1]
        assert call_args['token'] == self.token
        assert call_args['name'] == "Test Event"
        assert call_args['contract_id'] == 1
        assert call_args['client_id'] == 1
        assert call_args['location'] == "Test Location"
        assert call_args['attendees'] == 10
        assert call_args['notes'] == "Test Notes"
        assert call_args['support_contact_id'] is None
        assert isinstance(call_args['start_event'], datetime)
        assert isinstance(call_args['end_event'], datetime)
        assert call_args['end_event'] > call_args['start_event']
        assert (call_args['end_event'] - call_args['start_event']).total_seconds() == 7200  # 2 heures
    
    @patch('epiceventsCRM.views.event_view.click.prompt')
    @patch('epiceventsCRM.views.event_view.click.confirm')
    def test_create_event_with_specific_support_contact(self, mock_confirm, mock_prompt):
        """Test de création d'un événement avec un contact support spécifique"""
        # Configuration des mocks
        self.contract_controller.list_contracts.return_value = (True, [self.contract])
        mock_prompt.side_effect = [
            1,  # contract_index
            "Test Event",  # name
            "Test Location",  # location
            10,  # attendees
            "Test Notes",  # notes
            2  # support_contact_id
        ]
        mock_confirm.return_value = True  # Assigner un contact support spécifique
        self.event_controller.create_event.return_value = (True, self.event)
        
        # Appel de la méthode à tester
        self.view.create_event()
        
        # Vérifications
        self.contract_controller.list_contracts.assert_called_once_with(self.token)
        assert mock_prompt.call_count == 6
        self.event_controller.create_event.assert_called_once()
        call_args = self.event_controller.create_event.call_args[1]
        assert call_args['token'] == self.token
        assert call_args['name'] == "Test Event"
        assert call_args['contract_id'] == 1
        assert call_args['client_id'] == 1
        assert call_args['location'] == "Test Location"
        assert call_args['attendees'] == 10
        assert call_args['notes'] == "Test Notes"
        assert call_args['support_contact_id'] == 2
        assert isinstance(call_args['start_event'], datetime)
        assert isinstance(call_args['end_event'], datetime)
        assert call_args['end_event'] > call_args['start_event']
        assert (call_args['end_event'] - call_args['start_event']).total_seconds() == 7200  # 2 heures
    
    @patch('epiceventsCRM.views.event_view.click.prompt')
    def test_create_event_no_contracts(self, mock_prompt):
        """Test de création d'un événement sans contrats disponibles"""
        # Configuration des mocks
        self.contract_controller.list_contracts.return_value = (True, [])
        
        # Appel de la méthode à tester
        self.view.create_event()
        
        # Vérifications
        self.contract_controller.list_contracts.assert_called_once_with(self.token)
        mock_prompt.assert_not_called()
        self.event_controller.create_event.assert_not_called()
        
        # Vérifier l'affichage du message
        self.mock_echo.assert_any_call("Aucun contrat trouvé. Veuillez d'abord créer un contrat.")
    
    @patch('epiceventsCRM.views.event_view.click.prompt')
    @patch('epiceventsCRM.views.event_view.click.confirm')
    def test_create_event_error(self, mock_confirm, mock_prompt):
        """Test de création d'un événement avec erreur du contrôleur"""
        # Configuration des mocks
        self.contract_controller.list_contracts.return_value = (True, [self.contract])
        mock_prompt.side_effect = [
            1,  # contract_index
            "Test Event",  # name
            "Test Location",  # location
            10,  # attendees
            "Test Notes"  # notes
        ]
        mock_confirm.return_value = False  # Pas de contact support spécifique
        self.event_controller.create_event.return_value = (False, "Erreur de création")
        
        # Appel de la méthode à tester
        self.view.create_event()
        
        # Vérifications
        self.contract_controller.list_contracts.assert_called_once_with(self.token)
        assert mock_prompt.call_count == 5
        self.event_controller.create_event.assert_called_once()
        
        # Vérifier l'affichage de l'erreur
        self.mock_echo.assert_any_call("Erreur: Erreur de création")
    
    @patch('epiceventsCRM.views.event_view.click.prompt')
    @patch('epiceventsCRM.views.event_view.click.confirm')
    def test_update_event_success(self, mock_confirm, mock_prompt):
        """Test de mise à jour d'un événement (succès)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (True, self.event)
        mock_prompt.side_effect = [
            "Updated Event",  # name
            "Updated Location",  # location
            20,  # attendees
            "Updated Notes"  # notes
        ]
        mock_confirm.return_value = True  # Confirmer la mise à jour
        self.event_controller.update_event.return_value = (True, self.updated_event)
        
        # Appel de la méthode à tester
        self.view.update_event(1)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 1)
        assert mock_prompt.call_count == 4
        self.event_controller.update_event.assert_called_once_with(
            token=self.token,
            event_id=1,
            name="Updated Event",
            location="Updated Location",
            attendees=20,
            notes="Updated Notes"
        )
        
        # Vérifier l'affichage du succès
        self.mock_echo.assert_any_call("Événement mis à jour avec succès.")
    
    def test_update_event_not_found(self):
        """Test de mise à jour d'un événement non trouvé"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (False, "Événement non trouvé")
        
        # Appel de la méthode à tester
        self.view.update_event(999)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 999)
        self.event_controller.update_event.assert_not_called()
        
        # Vérifier l'affichage de l'erreur
        self.mock_echo.assert_any_call("Erreur: Événement non trouvé")
    
    @patch('epiceventsCRM.views.event_view.click.confirm')
    def test_delete_event_confirmed(self, mock_confirm):
        """Test de suppression d'un événement (confirmé)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (True, self.event)
        mock_confirm.return_value = True  # Confirmer la suppression
        self.event_controller.delete_event.return_value = (True, True)
        
        # Appel de la méthode à tester
        self.view.delete_event(1)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 1)
        self.event_controller.delete_event.assert_called_once_with(self.token, 1)
        
        # Vérifier l'affichage du succès
        self.mock_echo.assert_any_call("Événement supprimé avec succès.")
    
    @patch('epiceventsCRM.views.event_view.click.confirm')
    def test_delete_event_cancelled(self, mock_confirm):
        """Test de suppression d'un événement (annulé)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (True, self.event)
        mock_confirm.return_value = False  # Annuler la suppression
        
        # Appel de la méthode à tester
        self.view.delete_event(1)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 1)
        self.event_controller.delete_event.assert_not_called()
        
        # Vérifier l'affichage du message d'annulation
        self.mock_echo.assert_any_call("Suppression annulée.")
    
    @patch('epiceventsCRM.views.event_view.click.confirm')
    def test_delete_event_error(self, mock_confirm):
        """Test de suppression d'un événement (erreur)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (True, self.event)
        mock_confirm.return_value = True  # Confirmer la suppression
        self.event_controller.delete_event.return_value = (False, "Erreur de suppression")
        
        # Appel de la méthode à tester
        self.view.delete_event(1)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 1)
        self.event_controller.delete_event.assert_called_once_with(self.token, 1)
        
        # Vérifier l'affichage de l'erreur
        self.mock_echo.assert_any_call("Erreur: Erreur de suppression")
    
    @patch('epiceventsCRM.views.event_view.click.prompt')
    def test_assign_support_contact_success(self, mock_prompt):
        """Test d'assignation d'un contact support (succès)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (True, self.event)
        mock_prompt.return_value = 2  # support_contact_id
        self.event_controller.assign_support_contact.return_value = (True, self.event)
        
        # Appel de la méthode à tester
        self.view.assign_support_contact(1)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 1)
        mock_prompt.assert_called_once()
        self.event_controller.assign_support_contact.assert_called_once_with(
            token=self.token,
            event_id=1,
            support_contact_id=2
        )
        
        # Vérifier l'affichage du succès
        self.mock_echo.assert_any_call("Contact support assigné avec succès.")
    
    def test_assign_support_contact_event_not_found(self):
        """Test d'assignation d'un contact support (événement non trouvé)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (False, "Événement non trouvé")
        
        # Appel de la méthode à tester
        self.view.assign_support_contact(999)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 999)
        self.event_controller.assign_support_contact.assert_not_called()
        
        # Vérifier l'affichage de l'erreur
        self.mock_echo.assert_any_call("Erreur: Événement non trouvé")
    
    @patch('epiceventsCRM.views.event_view.click.prompt')
    def test_assign_support_contact_error(self, mock_prompt):
        """Test d'assignation d'un contact support (erreur)"""
        # Configuration des mocks
        self.event_controller.get_event.return_value = (True, self.event)
        mock_prompt.return_value = 2  # support_contact_id
        self.event_controller.assign_support_contact.return_value = (False, "Erreur d'assignation")
        
        # Appel de la méthode à tester
        self.view.assign_support_contact(1)
        
        # Vérifications
        self.event_controller.get_event.assert_called_once_with(self.token, 1)
        mock_prompt.assert_called_once()
        self.event_controller.assign_support_contact.assert_called_once_with(
            token=self.token,
            event_id=1,
            support_contact_id=2
        )
        
        # Vérifier l'affichage de l'erreur
        self.mock_echo.assert_any_call("Erreur: Erreur d'assignation")


class TestEventViewCLI:
    """Tests pour les commandes CLI de EventView"""

    def setup_method(self):
        """Configuration initiale avant chaque test"""
        self.session = MagicMock()
        self.token = "fake_token"
        self.view = MagicMock(spec=EventView)
    
    @patch('epiceventsCRM.views.event_view.EventView')
    def test_register_commands(self, mock_view_class):
        """Test d'enregistrement des commandes"""
        # Configuration du mock
        mock_view_class.return_value = self.view
        
        # Créer un groupe de commandes
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        EventView.register_commands(cli, lambda: self.session, lambda: self.token)
        
        # Vérifier que les commandes sont enregistrées
        assert 'events' in cli.commands
        assert 'list-events' in cli.commands['events'].commands
        assert 'get-event' in cli.commands['events'].commands
        assert 'create-event' in cli.commands['events'].commands
        assert 'update-event' in cli.commands['events'].commands
        assert 'delete-event' in cli.commands['events'].commands
        assert 'assign-support' in cli.commands['events'].commands
    
    @patch('epiceventsCRM.views.event_view.EventView')
    def test_list_command(self, mock_view_class):
        """Test de la commande list-events"""
        # Configuration du mock
        mock_view_class.return_value = self.view
        
        # Créer un groupe de commandes
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        EventView.register_commands(cli, lambda: self.session, lambda: self.token)
        
        # Créer un runner pour tester les commandes
        runner = CliRunner()
        
        # Exécuter la commande
        result = runner.invoke(cli, ['events', 'list-events'])
        
        # Vérifications
        assert result.exit_code == 0
        self.view.list_events.assert_called_once()
    
    @patch('epiceventsCRM.views.event_view.EventView')
    def test_get_command(self, mock_view_class):
        """Test de la commande get-event"""
        # Configuration du mock
        mock_view_class.return_value = self.view
        
        # Créer un groupe de commandes
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        EventView.register_commands(cli, lambda: self.session, lambda: self.token)
        
        # Créer un runner pour tester les commandes
        runner = CliRunner()
        
        # Exécuter la commande
        result = runner.invoke(cli, ['events', 'get-event', '1'])
        
        # Vérifications
        assert result.exit_code == 0
        self.view.get_event_by_id.assert_called_once_with(1)
    
    @patch('epiceventsCRM.views.event_view.EventView')
    def test_create_command(self, mock_view_class):
        """Test de la commande create-event"""
        # Configuration du mock
        mock_view_class.return_value = self.view
        
        # Créer un groupe de commandes
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        EventView.register_commands(cli, lambda: self.session, lambda: self.token)
        
        # Créer un runner pour tester les commandes
        runner = CliRunner()
        
        # Exécuter la commande
        result = runner.invoke(cli, ['events', 'create-event'])
        
        # Vérifications
        assert result.exit_code == 0
        self.view.create_event.assert_called_once()
    
    @patch('epiceventsCRM.views.event_view.EventView')
    def test_update_command(self, mock_view_class):
        """Test de la commande update-event"""
        # Configuration du mock
        mock_view_class.return_value = self.view
        
        # Créer un groupe de commandes
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        EventView.register_commands(cli, lambda: self.session, lambda: self.token)
        
        # Créer un runner pour tester les commandes
        runner = CliRunner()
        
        # Exécuter la commande
        result = runner.invoke(cli, ['events', 'update-event', '1'])
        
        # Vérifications
        assert result.exit_code == 0
        self.view.update_event.assert_called_once_with(1)
    
    @patch('epiceventsCRM.views.event_view.EventView')
    def test_delete_command(self, mock_view_class):
        """Test de la commande delete-event"""
        # Configuration du mock
        mock_view_class.return_value = self.view
        
        # Créer un groupe de commandes
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        EventView.register_commands(cli, lambda: self.session, lambda: self.token)
        
        # Créer un runner pour tester les commandes
        runner = CliRunner()
        
        # Exécuter la commande
        result = runner.invoke(cli, ['events', 'delete-event', '1'])
        
        # Vérifications
        assert result.exit_code == 0
        self.view.delete_event.assert_called_once_with(1)
    
    @patch('epiceventsCRM.views.event_view.EventView')
    def test_assign_support_command(self, mock_view_class):
        """Test de la commande assign-support"""
        # Configuration du mock
        mock_view_class.return_value = self.view
        
        # Créer un groupe de commandes
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        EventView.register_commands(cli, lambda: self.session, lambda: self.token)
        
        # Créer un runner pour tester les commandes
        runner = CliRunner()
        
        # Exécuter la commande
        result = runner.invoke(cli, ['events', 'assign-support', '1'])
        
        # Vérifications
        assert result.exit_code == 0
        self.view.assign_support_contact.assert_called_once_with(1)
    
    @patch('epiceventsCRM.views.event_view.EventView')
    def test_command_without_token(self, mock_view_class):
        """Test d'une commande sans token"""
        # Configuration du mock
        mock_view_class.return_value = self.view
        
        # Créer un groupe de commandes
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes avec un token None
        EventView.register_commands(cli, lambda: self.session, lambda: None)
        
        # Créer un runner pour tester les commandes
        runner = CliRunner()
        
        # Exécuter la commande
        result = runner.invoke(cli, ['events', 'list-events'])
        
        # Vérifications
        assert result.exit_code == 1
        assert "Vous devez être connecté pour effectuer cette action." in result.output 