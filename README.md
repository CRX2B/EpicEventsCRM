# Epic Events CRM

## Description
Epic Events CRM est une application en ligne de commande (CLI) développée pour Epic Events, une entreprise spécialisée dans l'organisation d'événements. Elle permet aux différents départements (commercial, support, gestion) de gérer les clients, contrats et événements avec un système de permissions différenciées.

## Schéma de la base de données
![Schéma UML de la base de données](Classe%20UML.png)

## Architecture du projet
L'application est structurée selon le pattern MVC (Modèle-Vue-Contrôleur) avec une couche d'accès aux données (DAO):

```
epiceventsCRM/
├── models/         # Modèles de données (SQLAlchemy ORM)
├── dao/            # Data Access Objects - Accès à la base de données
├── controllers/    # Logique métier et règles d'accès
├── views/          # Interface CLI (Click)
├── utils/          # Utilitaires (authentification, permissions, journalisation)
└── tests/          # Tests unitaires et d'intégration
```

## Fonctionnalités principales

- **Authentification par JWT** avec système de permissions par département
- **Gestion des utilisateurs** (création, modification, suppression)
- **Gestion des clients** avec attribution aux commerciaux
- **Gestion des contrats** liés aux clients
- **Gestion des événements** avec attribution de support

## Installation et déploiement

### Prérequis
- Python 3.9 ou supérieur
- PostgreSQL

### Étapes d'installation

1. **Cloner le dépôt Git**
   ```bash
   git clone <URL_DU_REPO>
   cd Epic-Events-CRM
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv env
   # Activation sous Windows
   env\Scripts\activate
   # Activation sous Linux/Mac
   source env/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**
   - Copier le fichier d'exemple:
     ```bash
     cp .env.example .env
     ```
   - Modifier les valeurs dans `.env`:
     - Informations de connexion PostgreSQL (DB_NAME, DB_USER, etc.)
     - Clé secrète JWT et algorithme
     - Identifiants administrateur initial
     - DSN Sentry (pour la journalisation)

5. **Initialiser la base de données**
   ```bash
   python -m epiceventsCRM.init_db
   ```
   Cette commande crée:
   - La structure des tables
   - Les départements (commercial, support, gestion)
   - Un utilisateur administrateur initial

### Utilisation rapide

Pour faciliter l'utilisation, un script `ecrm.bat` est disponible:

```bash
# Afficher l'aide
.\ecrm.bat --help

# Se connecter
.\ecrm.bat auth login

# Lister les clients
.\ecrm.bat client list-clients
```

Pour la liste complète des commandes, consultez le fichier `COMMANDS.md`.

## Sécurité et bonnes pratiques

- **Authentification**: Tokens JWT avec expiration
- **Stockage des mots de passe**: Hachage bcrypt avec salage
- **Contrôle d'accès**: Système de permissions par département
- **Protection contre les injections SQL**: Utilisation de l'ORM SQLAlchemy
- **Journalisation**: Capture des exceptions avec Sentry
- **Validation des données**: Vérification et nettoyage des entrées utilisateur

## Tests

Des tests automatisés couvrent la logique métier et les fonctionnalités critiques:

```bash
# Exécuter tous les tests
pytest

# Exécuter avec rapport de couverture
pytest --cov=epiceventsCRM --cov-report=html
```

## Spécificités techniques

- **ORM**: SQLAlchemy pour la manipulation de la base de données
- **CLI**: Click pour l'interface en ligne de commande
- **Authentification**: PyJWT pour la gestion des tokens
- **Affichage**: Rich pour une interface utilisateur améliorée
- **Journalisation**: Sentry pour le suivi des erreurs

## Licence
Ce projet est développé dans le cadre d'un projet de formation.