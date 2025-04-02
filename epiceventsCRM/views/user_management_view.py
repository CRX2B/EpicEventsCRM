from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import click
from epiceventsCRM.controllers.user_management_controller import UserManagementController
from epiceventsCRM.models.models import User

class UserManagementView:
    """
    Vue pour la gestion des utilisateurs.
    """
    
    def __init__(self):
        self.controller = UserManagementController()
    
    def display_user(self, user: User) -> None:
        """
        Affiche les informations d'un utilisateur.
        
        Args:
            user (User): L'utilisateur à afficher
        """
        print("\n=== Informations de l'utilisateur ===")
        print(f"ID: {user.id}")
        print(f"Nom complet: {user.fullname}")
        print(f"Email: {user.email}")
        print(f"Département: {user.department.departement_name if user.department else 'Non assigné'}")
        print("================================\n")
    
    def display_users(self, users: List[User]) -> None:
        """
        Affiche une liste d'utilisateurs.
        
        Args:
            users (List[User]): La liste des utilisateurs à afficher
        """
        if not users:
            print("\nAucun utilisateur trouvé.")
            return
            
        print("\n=== Liste des utilisateurs ===")
        for user in users:
            print(f"\nID: {user.id}")
            print(f"Nom complet: {user.fullname}")
            print(f"Email: {user.email}")
            print(f"Département: {user.department.departement_name if user.department else 'Non assigné'}")
        print("\n===========================\n")
    
    def get_user_input(self) -> Dict:
        """
        Récupère les informations d'un utilisateur depuis l'entrée utilisateur.
        
        Returns:
            Dict: Les données de l'utilisateur
        """
        print("\n=== Création d'un utilisateur ===")
        fullname = input("Nom complet: ")
        email = input("Email: ")
        password = input("Mot de passe: ")
        departement_id = int(input("ID du département (1: commercial, 2: support, 3: gestion): "))
        
        return {
            "fullname": fullname,
            "email": email,
            "password": password,
            "departement_id": departement_id
        }
    
    def get_user_update_input(self) -> Dict:
        """
        Récupère les informations de mise à jour d'un utilisateur.
        
        Returns:
            Dict: Les données de mise à jour
        """
        print("\n=== Mise à jour d'un utilisateur ===")
        print("Laissez vide pour ne pas modifier le champ")
        
        fullname = input("Nouveau nom complet: ")
        email = input("Nouvel email: ")
        password = input("Nouveau mot de passe: ")
        departement_id = input("Nouvel ID de département: ")
        
        update_data = {}
        if fullname:
            update_data["fullname"] = fullname
        if email:
            update_data["email"] = email
        if password:
            update_data["password"] = password
        if departement_id:
            update_data["departement_id"] = int(departement_id)
            
        return update_data
    
    def create_user(self, db: Session, token: str) -> Optional[User]:
        """
        Crée un nouvel utilisateur.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            
        Returns:
            Optional[User]: L'utilisateur créé
        """
        user_data = self.get_user_input()
        user = self.controller.create_user(db, token, user_data)
        
        if user:
            print("\nUtilisateur créé avec succès!")
            self.display_user(user)
        else:
            print("\nErreur: Vous n'avez pas la permission de créer des utilisateurs.")
            
        return user
    
    def get_user(self, db: Session, token: str) -> Optional[User]:
        """
        Récupère un utilisateur par son ID.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            
        Returns:
            Optional[User]: L'utilisateur trouvé
        """
        user_id = int(input("\nEntrez l'ID de l'utilisateur: "))
        user = self.controller.get_user(db, token, user_id)
        
        if user:
            self.display_user(user)
        else:
            print("\nUtilisateur non trouvé ou vous n'avez pas la permission de le consulter.")
            
        return user
    
    def list_users(self, db: Session, token: str) -> List[User]:
        """
        Affiche la liste des utilisateurs.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            
        Returns:
            List[User]: La liste des utilisateurs
        """
        skip = int(input("\nNombre d'utilisateurs à sauter (0 par défaut): ") or "0")
        limit = int(input("Nombre maximum d'utilisateurs à afficher (100 par défaut): ") or "100")
        
        users = self.controller.get_all_users(db, token, skip=skip, limit=limit)
        self.display_users(users)
        return users
    
    def update_user(self, db: Session, token: str) -> Optional[User]:
        """
        Met à jour un utilisateur.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            
        Returns:
            Optional[User]: L'utilisateur mis à jour
        """
        user_id = int(input("\nEntrez l'ID de l'utilisateur à mettre à jour: "))
        update_data = self.get_user_update_input()
        
        if not update_data:
            print("\nAucune modification à apporter.")
            return None
            
        user = self.controller.update_user(db, token, user_id, update_data)
        
        if user:
            print("\nUtilisateur mis à jour avec succès!")
            self.display_user(user)
        else:
            print("\nErreur: Utilisateur non trouvé ou vous n'avez pas la permission de le modifier.")
            
        return user
    
    def delete_user(self, db: Session, token: str) -> bool:
        """
        Supprime un utilisateur.
        
        Args:
            db (Session): La session de base de données
            token (str): Le token JWT
            
        Returns:
            bool: True si l'utilisateur a été supprimé
        """
        user_id = int(input("\nEntrez l'ID de l'utilisateur à supprimer: "))
        
        if self.controller.delete_user(db, token, user_id):
            print("\nUtilisateur supprimé avec succès!")
            return True
        else:
            print("\nErreur: Utilisateur non trouvé ou vous n'avez pas la permission de le supprimer.")
            return False
            
    @staticmethod
    def register_commands(cli_group, get_session, get_token):
        """
        Enregistre les commandes CLI pour la gestion des utilisateurs
        
        Args:
            cli_group: Groupe de commandes Click
            get_session: Fonction pour obtenir une session DB
            get_token: Fonction pour obtenir le token JWT
        """
        
        @cli_group.group()
        def user():
            """Gestion des utilisateurs"""
            pass
        
        @user.command("list")
        def list_users():
            """Liste tous les utilisateurs accessibles"""
            session = get_session()
            token = get_token()
            if not token:
                print("Erreur: Vous devez être connecté pour accéder aux utilisateurs.")
                return
            user_view = UserManagementView()
            user_view.list_users(session, token)
        
        @user.command("get")
        def get_user():
            """Affiche les détails d'un utilisateur spécifique"""
            session = get_session()
            token = get_token()
            if not token:
                print("Erreur: Vous devez être connecté pour accéder aux utilisateurs.")
                return
            user_view = UserManagementView()
            user_view.get_user(session, token)
        
        @user.command("create")
        def create_user():
            """Crée un nouvel utilisateur"""
            session = get_session()
            token = get_token()
            if not token:
                print("Erreur: Vous devez être connecté pour créer un utilisateur.")
                return
            user_view = UserManagementView()
            user_view.create_user(session, token)
        
        @user.command("update")
        def update_user():
            """Met à jour un utilisateur existant"""
            session = get_session()
            token = get_token()
            if not token:
                print("Erreur: Vous devez être connecté pour mettre à jour un utilisateur.")
                return
            user_view = UserManagementView()
            user_view.update_user(session, token)
        
        @user.command("delete")
        def delete_user():
            """Supprime un utilisateur existant"""
            session = get_session()
            token = get_token()
            if not token:
                print("Erreur: Vous devez être connecté pour supprimer un utilisateur.")
                return
            user_view = UserManagementView()
            user_view.delete_user(session, token) 