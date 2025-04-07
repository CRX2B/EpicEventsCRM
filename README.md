# Epic Events CRM

## Description
Epic Events CRM est une application de gestion de la relation client (CRM) développée en Python. Elle permet de gérer les clients, les contrats et les événements d'Epic Events, avec un système de permissions basé sur les départements.

## Structure du Projet
```
epiceventsCRM/
├── controllers/     # Contrôleurs de l'application
├── dao/            # Couche d'accès aux données
├── models/         # Modèles de données
├── utils/          # Utilitaires (authentification, permissions)
├── views/          # Vues CLI
└── tests/          # Tests unitaires et fonctionnels
```

## Fonctionnalités

### Authentification
- Système de connexion sécurisé avec JWT (JSON Web Tokens)
- Gestion des sessions utilisateurs
- Protection des routes avec système de permissions

### Gestion des Utilisateurs
- Création, modification et suppression des utilisateurs
- Attribution des départements
- Gestion des permissions par département

### Gestion des Clients
- Création de nouveaux clients
- Modification des informations client
- Suppression de clients
- Consultation des clients

### Gestion des Contrats
- Création de contrats
- Modification des contrats
- Suppression de contrats
- Consultation des contrats

### Gestion des Événements
- Création d'événements
- Modification des événements
- Attribution des supports
- Consultation des événements

## Permissions par Département

### Département Commercial
- Gestion complète des clients (CRUD)
- Création d'événements
- Mise à jour des contrats de ses clients
- Lecture des clients, contrats et événements

### Département Support
- Mise à jour des événements dont ils sont responsables
- Lecture des clients, contrats et événements

### Département Gestion
- Gestion complète des utilisateurs (CRUD)
- Gestion complète des contrats (CRUD)
- Attribution des supports aux événements
- Lecture des clients, contrats et événements

## Installation

1. Cloner le repository :
```bash
git clone [URL_DU_REPO]
cd epiceventsCRM
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer la base de données et les variables d'environnement :
- Créer un fichier `.env` à partir du modèle `.env.example` :
```bash
cp .env.example .env
```
- Modifier les valeurs dans le fichier `.env` avec vos propres informations :
  - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, etc. : informations de connexion à la base de données
  - `JWT_SECRET` : clé secrète pour la génération des tokens JWT
  - `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_FULLNAME` : identifiants de l'administrateur par défaut

5. Initialiser la base de données :
```bash
python -m epiceventsCRM.init_db
```

## Utilisation

### Démarrage de l'application
```bash
python -m epiceventsCRM.main
```

### Commandes CLI disponibles
- `login` : Connexion à l'application
- `logout` : Déconnexion
- `create-user` : Création d'un utilisateur (gestion uniquement)
- `list-users` : Liste des utilisateurs (gestion uniquement)
- `create-client` : Création d'un client (commercial uniquement)
- `list-clients` : Liste des clients
- `create-contract` : Création d'un contrat (gestion uniquement)
- `list-contracts` : Liste des contrats
- `create-event` : Création d'un événement (commercial uniquement)
- `list-events` : Liste des événements

## Utilisation simplifiée des commandes

Pour simplifier l'utilisation des commandes, un script batch `ecrm.bat` est fourni à la racine du projet. Ce script vous permet d'éviter de taper `python -m epiceventsCRM.main` à chaque fois.

### Utilisation sous Windows

Au lieu de :
```bash
python -m epiceventsCRM.main event create --contract 1 --name "Conférence" --start-date "2024-06-01 09:00" --end-date "2024-06-01 18:00" --location "Paris" --attendees 100
```

Vous pouvez simplement utiliser :
```bash
.\ecrm.bat event create --contract 1 --name "Conférence" --start-date "2024-06-01 09:00" --end-date "2024-06-01 18:00" --location "Paris" --attendees 100
```

Quelques exemples :
```bash
# Afficher l'aide
.\ecrm.bat --help

# Se connecter
.\ecrm.bat auth login

# Lister les événements
.\ecrm.bat event list-events
```

### Conseils pour PowerShell

Si vous utilisez PowerShell régulièrement, vous pouvez également créer un alias pour éviter de taper `.\ecrm.bat` :

```powershell
Set-Alias -Name ecrm -Value ".\ecrm.bat"
```

Ensuite, vous pouvez simplement utiliser :
```powershell
ecrm event create --contract 1 --name "Conférence" ...
```

Notez que cet alias ne persiste que pour la session PowerShell en cours. Pour le rendre permanent, vous devrez l'ajouter à votre profil PowerShell.

## Tests
Pour exécuter les tests :
```bash
python -m pytest
```

Les tests couvrent :
- Tests d'authentification
- Tests de permissions
- Tests des contrôleurs
- Tests des vues CLI

## Sécurité
- Authentification par JWT
- Hachage des mots de passe
- Système de permissions par département
- Protection des routes sensibles

## Contribution
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence
Ce projet est sous licence MIT.