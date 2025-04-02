import pytest
from unittest.mock import MagicMock, patch
import click
from click.testing import CliRunner
from datetime import datetime

from epiceventsCRM.views.contract_view import ContractView
from epiceventsCRM.controllers.contract_controller import ContractController
from epiceventsCRM.controllers.client_controller import ClientController
from epiceventsCRM.models.models import Contract, Client, User


class TestContractView:
    """Tests pour la classe ContractView"""

    def setup_method(self):
        """Configuration initiale avant chaque test"""
        self.session = MagicMock()
        self.token = "fake_token"
        self.contract_controller = MagicMock(spec=ContractController)
        self.client_controller = MagicMock(spec=ClientController)
        
        # Création de l'objet à tester
        self.view = ContractView(self.session, self.token)
        self.view.contract_controller = self.contract_controller
        self.view.client_controller = self.client_controller
        
        # Création d'objets de test
        commercial = User(
            id=1,
            fullname="Commercial Test",
            email="commercial@test.com",
            password="password",
            departement_id=1
        )
        
        self.client = Client(
            id=1,
            fullname="Client Test",
            email="client@test.com",
            phone_number=123456789,
            enterprise="Enterprise Test",
            create_date=datetime.now(),
            sales_contact_id=1,
            sales_contact=commercial
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
            sales_contact=commercial
        )
        
        self.updated_contract = Contract(
            id=1,
            client_id=1,
            amount=2000.0,
            remaining_amount=1500.0,
            create_date=datetime.now(),
            status=True,
            sales_contact_id=1,
            client=self.client,
            sales_contact=commercial
        )
        
        # Créer un mock pour click.echo pour ne pas polluer la sortie des tests
        self.echo_patch = patch('epiceventsCRM.views.contract_view.click.echo')
        self.mock_echo = self.echo_patch.start()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        self.echo_patch.stop()
    
    def test_display_contract(self):
        """Test d'affichage des détails d'un contrat"""
        # Appel de la méthode à tester
        self.view.display_contract(self.contract)
        
        # Vérifier que click.echo a été appelé avec les bonnes informations
        assert self.mock_echo.call_count >= 7  # Au moins 7 appels pour afficher les détails
        
        # Vérifier que les informations importantes sont affichées
        call_args_list = [call[0][0] for call in self.mock_echo.call_args_list]
        assert any(f"ID: {self.contract.id}" in str(arg) for arg in call_args_list)
        assert any(f"Client ID: {self.contract.client_id}" in str(arg) for arg in call_args_list)
        assert any(f"Montant total: {self.contract.amount}" in str(arg) for arg in call_args_list)
        assert any(f"Montant restant: {self.contract.remaining_amount}" in str(arg) for arg in call_args_list)
        assert any(f"Statut: {'Signé' if self.contract.status else 'Non signé'}" in str(arg) for arg in call_args_list)
        assert any(f"Commercial ID: {self.contract.sales_contact_id}" in str(arg) for arg in call_args_list)
    
    def test_list_contracts_success(self):
        """Test de listage des contrats (succès)"""
        # Configuration des mocks
        self.contract_controller.list_contracts.return_value = (True, [self.contract])
        
        # Appel de la méthode à tester
        self.view.list_contracts()
        
        # Vérifications
        self.contract_controller.list_contracts.assert_called_once_with(self.token)
        
        # Vérifier que click.echo a été appelé pour afficher les contrats
        assert self.mock_echo.call_count > 0
        
        # Vérifier l'affichage du nombre de contrats trouvés
        call_args_list = [call[0][0] for call in self.mock_echo.call_args_list]
        assert any("Liste des contrats (1 trouvés)" in str(arg) for arg in call_args_list)
    
    def test_list_contracts_empty(self):
        """Test de listage des contrats (aucun contrat)"""
        # Configuration des mocks
        self.contract_controller.list_contracts.return_value = (True, [])
        
        # Appel de la méthode à tester
        self.view.list_contracts()
        
        # Vérifications
        self.contract_controller.list_contracts.assert_called_once_with(self.token)
        
        # Vérifier que click.echo a été appelé pour afficher le message
        self.mock_echo.assert_any_call("Aucun contrat trouvé.")
    
    def test_list_contracts_error(self):
        """Test de listage des contrats (erreur)"""
        # Configuration des mocks
        self.contract_controller.list_contracts.return_value = (False, "Erreur d'accès")
        
        # Appel de la méthode à tester
        self.view.list_contracts()
        
        # Vérifications
        self.contract_controller.list_contracts.assert_called_once_with(self.token)
        
        # Vérifier que click.echo a été appelé pour afficher l'erreur
        self.mock_echo.assert_any_call("Erreur: Erreur d'accès")
    
    def test_get_contract_by_id_success(self):
        """Test de récupération d'un contrat par ID (succès)"""
        # Configuration des mocks
        self.contract_controller.get_contract.return_value = (True, self.contract)
        
        # Appel de la méthode à tester
        self.view.get_contract_by_id(1)
        
        # Vérifications
        self.contract_controller.get_contract.assert_called_once_with(self.token, 1)
        
        # Vérifier que click.echo a été appelé pour afficher les détails
        assert self.mock_echo.call_count > 0
        
        # Vérifier l'affichage du titre
        call_args_list = [call[0][0] for call in self.mock_echo.call_args_list]
        assert any("Détails du contrat" in str(arg) for arg in call_args_list)
    
    def test_get_contract_by_id_error(self):
        """Test de récupération d'un contrat par ID (erreur)"""
        # Configuration des mocks
        self.contract_controller.get_contract.return_value = (False, "Contrat non trouvé")
        
        # Appel de la méthode à tester
        self.view.get_contract_by_id(999)
        
        # Vérifications
        self.contract_controller.get_contract.assert_called_once_with(self.token, 999)
        
        # Vérifier que click.echo a été appelé pour afficher l'erreur
        self.mock_echo.assert_any_call("Erreur: Contrat non trouvé")
    
    @patch('epiceventsCRM.views.contract_view.click.prompt')
    @patch('epiceventsCRM.views.contract_view.click.confirm')
    def test_create_contract_success(self, mock_confirm, mock_prompt):
        """Test de création d'un contrat (succès)"""
        # Configuration des mocks
        self.client_controller.list_clients.return_value = (True, [self.client])
        mock_prompt.side_effect = [1, 2000.0]  # Réponses aux prompts : client_index, amount
        
        mock_confirm.return_value = False  # Pas de commercial spécifique
        self.contract_controller.create_contract.return_value = (True, self.contract)
        
        # Appel de la méthode à tester
        self.view.create_contract()
        
        # Vérifications
        self.client_controller.list_clients.assert_called_once_with(self.token)
        assert mock_prompt.call_count == 2
        self.contract_controller.create_contract.assert_called_once_with(
            token=self.token,
            client_id=1,
            amount=2000.0,
            sales_contact_id=None
        )
    
    @patch('epiceventsCRM.views.contract_view.click.prompt')
    @patch('epiceventsCRM.views.contract_view.click.confirm')
    def test_create_contract_with_specific_sales_contact(self, mock_confirm, mock_prompt):
        """Test de création d'un contrat avec un commercial spécifique"""
        # Configuration des mocks
        self.client_controller.list_clients.return_value = (True, [self.client])
        mock_prompt.side_effect = [1, 2000.0, 2]  # Réponses: client_index, amount, sales_contact_id
        mock_confirm.return_value = True  # Assigner un commercial spécifique
        self.contract_controller.create_contract.return_value = (True, self.contract)
        
        # Appel de la méthode à tester
        self.view.create_contract()
        
        # Vérifications
        self.client_controller.list_clients.assert_called_once_with(self.token)
        assert mock_prompt.call_count == 3
        self.contract_controller.create_contract.assert_called_once_with(
            token=self.token,
            client_id=1,
            amount=2000.0,
            sales_contact_id=2
        )
    
    @patch('epiceventsCRM.views.contract_view.click.prompt')
    def test_create_contract_no_clients(self, mock_prompt):
        """Test de création d'un contrat sans clients disponibles"""
        # Configuration des mocks
        self.client_controller.list_clients.return_value = (True, [])
        
        # Appel de la méthode à tester
        self.view.create_contract()
        
        # Vérifications
        self.client_controller.list_clients.assert_called_once_with(self.token)
        mock_prompt.assert_not_called()
        self.contract_controller.create_contract.assert_not_called()
        
        # Vérifier l'affichage du message
        self.mock_echo.assert_any_call("Aucun client trouvé. Veuillez d'abord créer un client.")
    
    @patch('epiceventsCRM.views.contract_view.click.prompt')
    @patch('epiceventsCRM.views.contract_view.click.confirm')
    def test_create_contract_error(self, mock_confirm, mock_prompt):
        """Test de création d'un contrat avec erreur du contrôleur"""
        # Configuration des mocks
        self.client_controller.list_clients.return_value = (True, [self.client])
        mock_prompt.side_effect = [1, 2000.0]
        mock_confirm.return_value = False  # Pas de commercial spécifique
        self.contract_controller.create_contract.return_value = (False, "Erreur de création")
        
        # Rediriger stdout pour le tester
        with patch('epiceventsCRM.views.contract_view.click.echo') as mock_echo:
            # Appel de la méthode à tester
            self.view.create_contract()
            
            # Vérifications
            self.client_controller.list_clients.assert_called_once_with(self.token)
            assert mock_prompt.call_count == 2
            self.contract_controller.create_contract.assert_called_once_with(
                token=self.token,
                client_id=1,
                amount=2000.0,
                sales_contact_id=None
            )
            mock_echo.assert_any_call("Erreur: Erreur de création")
    
    @patch('epiceventsCRM.views.contract_view.click.confirm')
    def test_update_contract_success(self, mock_confirm):
        """Test de mise à jour d'un contrat (succès)"""
        # Configuration des mocks
        self.contract_controller.get_contract.return_value = (True, self.contract)
        mock_confirm.side_effect = [True, True, True, False]  # Les réponses pour les confirmations
        
        with patch('epiceventsCRM.views.contract_view.click.prompt') as mock_prompt:
            mock_prompt.side_effect = [2000.0, 1500.0]  # Nouveau montant, nouveau montant restant 
            
            # Statut est demandé via click.confirm, on ajoute un mock spécifique
            with patch.object(self.contract_controller, 'update_contract') as mock_update:
                mock_update.return_value = (True, self.updated_contract)
                
                # Appel de la méthode à tester
                self.view.update_contract(1)
                
                # Vérifications
                self.contract_controller.get_contract.assert_called_once_with(self.token, 1)
                
                mock_confirm.assert_any_call("Mettre à jour le montant?", default=False)
                mock_confirm.assert_any_call("Mettre à jour le montant restant?", default=False)
                
                mock_confirm.assert_any_call("Mettre à jour le statut?", default=False)
                
                # Vérifier les prompts pour les nouvelles valeurs
                mock_prompt.assert_any_call("Nouveau montant (€)", type=float)
                mock_prompt.assert_any_call("Nouveau montant restant (€)", type=float)
                
                # Vérifier l'appel au contrôleur pour la mise à jour
                expected_data = {
                    "amount": 2000.0,
                    "remaining_amount": 1500.0,
                    "status": False  # Corrigé pour correspondre au comportement réel
                }
                mock_update.assert_called_once_with(self.token, 1, expected_data)
                
                # Vérifier l'affichage du succès
                call_args_list = [call[0][0] for call in self.mock_echo.call_args_list]
                assert any("Contrat mis à jour avec succès" in str(arg) for arg in call_args_list)
    
    def test_update_contract_not_found(self):
        """Test de mise à jour d'un contrat inexistant"""
        # Configuration des mocks
        self.contract_controller.get_contract.return_value = (False, "Contrat non trouvé")
        
        # Appel de la méthode à tester
        self.view.update_contract(999)
        
        # Vérifications
        self.contract_controller.get_contract.assert_called_once_with(self.token, 999)
        self.mock_echo.assert_any_call("Erreur: Contrat non trouvé")
    
    @patch('epiceventsCRM.views.contract_view.click.confirm')
    def test_delete_contract_confirmed(self, mock_confirm):
        """Test de suppression d'un contrat (confirmé)"""
        # Configuration des mocks
        mock_confirm.return_value = True  # Confirmation de suppression
        self.contract_controller.delete_contract.return_value = (True, "Contrat supprimé avec succès")
        
        # Appel de la méthode à tester
        self.view.delete_contract(1)
        
        # Vérifications
        mock_confirm.assert_called_once_with("Êtes-vous sûr de vouloir supprimer le contrat 1?", default=False)
        self.contract_controller.delete_contract.assert_called_once_with(self.token, 1)
        self.mock_echo.assert_any_call("Contrat supprimé avec succès")
    
    @patch('epiceventsCRM.views.contract_view.click.confirm')
    def test_delete_contract_cancelled(self, mock_confirm):
        """Test de suppression d'un contrat (annulé)"""
        # Configuration des mocks
        mock_confirm.return_value = False  # Annulation de la suppression
        
        # Appel de la méthode à tester
        self.view.delete_contract(1)
        
        # Vérifications
        mock_confirm.assert_called_once_with("Êtes-vous sûr de vouloir supprimer le contrat 1?", default=False)
        self.contract_controller.delete_contract.assert_not_called()
        self.mock_echo.assert_any_call("Suppression annulée.")
    
    @patch('epiceventsCRM.views.contract_view.click.confirm')
    def test_delete_contract_error(self, mock_confirm):
        """Test de suppression d'un contrat avec erreur"""
        # Configuration des mocks
        mock_confirm.return_value = True  # Confirmation de suppression
        self.contract_controller.delete_contract.return_value = (False, "Erreur: Autorisation refusée")
        
        # Appel de la méthode à tester
        self.view.delete_contract(1)
        
        # Vérifications
        self.mock_echo.assert_any_call("Erreur: Erreur: Autorisation refusée")


class TestContractViewCLI:
    """Tests pour les commandes CLI de ContractView"""
    
    def setup_method(self):
        """Configuration initiale avant chaque test"""
        self.runner = CliRunner()
        
        # Préparer des mocks pour les fonctions externes
        self.get_session_mock = MagicMock()
        self.get_session_mock.return_value = MagicMock()
        
        self.get_token_mock = MagicMock()
        self.get_token_mock.return_value = "fake_token"
    
    @patch('epiceventsCRM.views.contract_view.ContractView')
    def test_register_commands(self, mock_view_class):
        """Test d'enregistrement des commandes CLI"""
        # Créer un groupe de commandes Click
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        ContractView.register_commands(cli, self.get_session_mock, self.get_token_mock)
        
        # Vérifier que le groupe de commandes a été créé
        assert "contract" in cli.commands
        
        # Vérifier les sous-commandes
        contract_group = cli.commands["contract"]
        assert "list" in contract_group.commands
        assert "get" in contract_group.commands
        assert "create" in contract_group.commands
        assert "update" in contract_group.commands
        assert "delete" in contract_group.commands
    
    @patch('epiceventsCRM.views.contract_view.ContractView')
    def test_list_command(self, mock_view_class):
        """Test de la commande list"""
        # Configurer le mock
        view_instance = mock_view_class.return_value
        
        # Créer un groupe de commandes Click
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        ContractView.register_commands(cli, self.get_session_mock, self.get_token_mock)
        
        # Exécuter la commande
        result = self.runner.invoke(cli, ["contract", "list"])
        
        # Vérifications
        assert result.exit_code == 0
        self.get_session_mock.assert_called_once()
        self.get_token_mock.assert_called_once()
        mock_view_class.assert_called_once_with(self.get_session_mock.return_value, self.get_token_mock.return_value)
        view_instance.list_contracts.assert_called_once()
    
    @patch('epiceventsCRM.views.contract_view.ContractView')
    def test_get_command(self, mock_view_class):
        """Test de la commande get"""
        # Configurer le mock
        view_instance = mock_view_class.return_value
        
        # Créer un groupe de commandes Click
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        ContractView.register_commands(cli, self.get_session_mock, self.get_token_mock)
        
        # Exécuter la commande
        result = self.runner.invoke(cli, ["contract", "get", "1"])
        
        # Vérifications
        assert result.exit_code == 0
        self.get_session_mock.assert_called_once()
        self.get_token_mock.assert_called_once()
        mock_view_class.assert_called_once_with(self.get_session_mock.return_value, self.get_token_mock.return_value)
        view_instance.get_contract_by_id.assert_called_once_with(1)
    
    @patch('epiceventsCRM.views.contract_view.ContractView')
    def test_create_command(self, mock_view_class):
        """Test de la commande create"""
        # Configurer le mock
        view_instance = mock_view_class.return_value
        
        # Créer un groupe de commandes Click
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        ContractView.register_commands(cli, self.get_session_mock, self.get_token_mock)
        
        # Exécuter la commande
        result = self.runner.invoke(cli, ["contract", "create"])
        
        # Vérifications
        assert result.exit_code == 0
        self.get_session_mock.assert_called_once()
        self.get_token_mock.assert_called_once()
        mock_view_class.assert_called_once_with(self.get_session_mock.return_value, self.get_token_mock.return_value)
        view_instance.create_contract.assert_called_once()
    
    @patch('epiceventsCRM.views.contract_view.ContractView')
    def test_update_command(self, mock_view_class):
        """Test de la commande update"""
        # Configurer le mock
        view_instance = mock_view_class.return_value
        
        # Créer un groupe de commandes Click
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        ContractView.register_commands(cli, self.get_session_mock, self.get_token_mock)
        
        # Exécuter la commande
        result = self.runner.invoke(cli, ["contract", "update", "1"])
        
        # Vérifications
        assert result.exit_code == 0
        self.get_session_mock.assert_called_once()
        self.get_token_mock.assert_called_once()
        mock_view_class.assert_called_once_with(self.get_session_mock.return_value, self.get_token_mock.return_value)
        view_instance.update_contract.assert_called_once_with(1)
    
    @patch('epiceventsCRM.views.contract_view.ContractView')
    def test_delete_command(self, mock_view_class):
        """Test de la commande delete"""
        # Configurer le mock
        view_instance = mock_view_class.return_value
        
        # Créer un groupe de commandes Click
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        ContractView.register_commands(cli, self.get_session_mock, self.get_token_mock)
        
        # Exécuter la commande
        result = self.runner.invoke(cli, ["contract", "delete", "1"])
        
        # Vérifications
        assert result.exit_code == 0
        self.get_session_mock.assert_called_once()
        self.get_token_mock.assert_called_once()
        mock_view_class.assert_called_once_with(self.get_session_mock.return_value, self.get_token_mock.return_value)
        view_instance.delete_contract.assert_called_once_with(1)
    
    @patch('epiceventsCRM.views.contract_view.ContractView')
    def test_command_without_token(self, mock_view_class):
        """Test d'une commande sans token"""
        # Configurer le mock
        self.get_token_mock.return_value = None
        
        # Créer un groupe de commandes Click
        @click.group()
        def cli():
            pass
        
        # Enregistrer les commandes
        ContractView.register_commands(cli, self.get_session_mock, self.get_token_mock)
        
        # Exécuter la commande
        result = self.runner.invoke(cli, ["contract", "list"])
        
        # Vérifications
        assert result.exit_code == 0
        # La session est toujours récupérée, même si le token est None
        self.get_session_mock.assert_called_once()
        self.get_token_mock.assert_called_once()
        # Mais la vue ContractView n'est pas instanciée
        mock_view_class.assert_not_called() 