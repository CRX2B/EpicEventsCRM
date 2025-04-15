# Commandes CLI Epic Events CRM

## Gestion des Utilisateurs

### Lister les Utilisateurs
```bash
.\ecrm.bat user list-users
```
**Description** : Affiche la liste de tous les utilisateurs avec pagination
**Options** :
- `--page` : Numéro de page à afficher (défaut: 1)
- `--page-size` : Nombre d'utilisateurs par page (défaut: 10)
**Permissions** : Département gestion uniquement
**Pagination** : 
- Les résultats sont paginés par défaut (10 éléments par page)
- Le nombre total d'utilisateurs est affiché
- Navigation possible entre les pages avec l'option --page

**Exemple** :
```bash
# Afficher la première page avec 10 utilisateurs par page (par défaut)
.\ecrm.bat user list-users

# Afficher la deuxième page avec 5 utilisateurs par page
.\ecrm.bat user list-users --page 2 --page-size 5
```

### Créer un Utilisateur
```bash
.\ecrm.bat user create
```
**Description** : Création d'un nouvel utilisateur
**Options** :
- `--fullname` ou `-f` : Nom complet de l'utilisateur (requis)
- `--email` ou `-e` : Adresse email de l'utilisateur (requis)
- `--password` ou `-p` : Mot de passe de l'utilisateur (requis)
- `--department` ou `-d` : ID du département (requis) : 1=commercial, 2=support, 3=gestion
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat user create --fullname "Jean Dupont" --email jean@epicevents.com --password "MotDePasseSecurise" --department 1
```

### Afficher un Utilisateur
```bash
.\ecrm.bat user get ID
```
**Description** : Affiche les détails d'un utilisateur spécifique
**Arguments** :
- `ID` : L'identifiant de l'utilisateur à afficher
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat user get 42
```

### Mettre à jour un Utilisateur
```bash
.\ecrm.bat user update ID
```
**Description** : Met à jour les informations d'un utilisateur
**Arguments** :
- `ID` : L'identifiant de l'utilisateur à mettre à jour
**Options** :
- `--email` ou `-e` : Nouvelle adresse email
- `--password` ou `-p` : Nouveau mot de passe
- `--fullname` : Nouveau nom complet
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat user update 42 --email new.email@example.com --fullname "Jane Smith"
```

### Supprimer un Utilisateur
```bash
.\ecrm.bat user delete-user ID
```
**Description** : Supprime un utilisateur
**Arguments** :
- `ID` : L'identifiant de l'utilisateur à supprimer
**Options** :
- `--confirm` : Confirme la suppression sans demander de confirmation interactive
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat user delete-user 42 --confirm
```

### Trouver un Utilisateur
```bash
.\ecrm.bat user find
```
**Description** : Recherche un utilisateur par son adresse email
**Options** :
- `--email` ou `-e` : L'adresse email à rechercher (requis)
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat user find --email john@example.com
```

## Gestion des Clients

### Créer un Client
```bash
.\ecrm.bat client create
```
**Description** : Création d'un nouveau client
**Options** :
- `--fullname` ou `-f` : Nom complet du client (requis)
- `--email` ou `-e` : Adresse email du client (requis)
- `--phone_number` ou `-p` : Numéro de téléphone (requis)
- `--enterprise` ou `-c` : Nom de l'entreprise (requis)
**Permissions** : Département commercial uniquement

**Exemple** :
```bash
.\ecrm.bat client create --fullname "Jane Smith" --email jane@company.com --phone_number "0123456789" --enterprise "ACME Corp"
```

### Lister les Clients
```bash
.\ecrm.bat client list-clients
```
**Description** : Affiche la liste de tous les clients avec pagination
**Options** :
- `--page` : Numéro de page à afficher (défaut: 1)
- `--page-size` : Nombre de clients par page (défaut: 10)
**Permissions** : Tous les départements
**Pagination** : 
- Les résultats sont paginés par défaut (10 éléments par page)
- Le nombre total de clients est affiché
- Navigation possible entre les pages avec l'option --page

**Exemple** :
```bash
# Afficher la première page avec 10 clients par page (par défaut)
.\ecrm.bat client list-clients

# Afficher la deuxième page avec 5 clients par page
.\ecrm.bat client list-clients --page 2 --page-size 5
```

### Afficher un Client
```bash
.\ecrm.bat client get-client ID
```
**Description** : Affiche les détails d'un client spécifique
**Arguments** :
- `ID` : L'identifiant du client à afficher
**Permissions** : Tous les départements

**Exemple** :
```bash
.\ecrm.bat client get-client 42
```

### Mettre à jour un Client
```bash
.\ecrm.bat client update ID
```
**Description** : Met à jour les informations d'un client
**Arguments** :
- `ID` : L'identifiant du client à mettre à jour
**Options** :
- `--fullname` ou `-f` : Nouveau nom complet
- `--email` ou `-e` : Nouvelle adresse email
- `--phone_number` ou `-p` : Nouveau numéro de téléphone
- `--enterprise` ou `-c` : Nouveau nom d'entreprise
**Permissions** : Département commercial (seulement pour ses clients) et département gestion

**Exemple** :
```bash
.\ecrm.bat client update 42 --email new.email@company.com --phone_number "9876543210"
```

### Supprimer un Client
```bash
.\ecrm.bat client delete-client ID
```
**Description** : Supprime un client
**Arguments** :
- `ID` : L'identifiant du client à supprimer
**Options** :
- `--confirm` : Confirme la suppression sans demander de confirmation interactive
**Permissions** : Département commercial (seulement pour ses clients) et département gestion

**Exemple** :
```bash
.\ecrm.bat client delete-client 42 --confirm
```

### Mes Clients
```bash
.\ecrm.bat client my-clients
```
**Description** : Affiche la liste des clients assignés au commercial connecté
**Options** : Aucune
**Permissions** : Département commercial uniquement

**Exemple** :
```bash
.\ecrm.bat client my-clients
```

## Gestion des Contrats

### Créer un Contrat
```bash
.\ecrm.bat contract create
```
**Description** : Création d'un nouveau contrat
**Options** :
- `--client` ou `-c` : ID du client (requis)
- `--amount` ou `-a` : Montant du contrat (requis)
- `--signed` ou `-s` : Marque le contrat comme signé (optionnel, drapeau)
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat contract create --client 1 --amount 10000 --signed
```

**Notes** :
- Le montant restant est automatiquement initialisé au montant total
- La date de création est automatiquement définie à la date actuelle
- Le commercial responsable est automatiquement assigné au commercial du client

### Lister les Contrats
```bash
.\ecrm.bat contract list-contracts
```
**Description** : Affiche la liste de tous les contrats avec pagination
**Options** :
- `--page` : Numéro de page à afficher (défaut: 1)
- `--page-size` : Nombre de contrats par page (défaut: 10)
**Permissions** : Tous les départements
**Pagination** : 
- Les résultats sont paginés par défaut (10 éléments par page)
- Le nombre total de contrats est affiché
- Navigation possible entre les pages avec l'option --page

**Exemple** :
```bash
# Afficher la première page avec 10 contrats par page (par défaut)
.\ecrm.bat contract list-contracts

# Afficher la deuxième page avec 5 contrats par page
.\ecrm.bat contract list-contracts --page 2 --page-size 5
```

### Afficher un Contrat
```bash
.\ecrm.bat contract get-contract ID
```
**Description** : Affiche les détails d'un contrat spécifique
**Arguments** :
- `ID` : L'identifiant du contrat à afficher
**Permissions** : Tous les départements

**Exemple** :
```bash
.\ecrm.bat contract get-contract 42
```

### Mettre à jour un Contrat
```bash
.\ecrm.bat contract update ID
```
**Description** : Met à jour les informations d'un contrat
**Arguments** :
- `ID` : L'identifiant du contrat à mettre à jour
**Options** :
- `--amount` ou `-a` : Nouveau montant du contrat
- `--remaining-amount` ou `-r` : Nouveau montant restant du contrat
- `--signed/--unsigned` : Marque le contrat comme signé ou non signé
**Permissions** : Département gestion et département commercial (seulement pour les contrats de ses clients)

**Exemple** :
```bash
# Mettre à jour le montant et le statut
.\ecrm.bat contract update 42 --amount 5000 --signed

# Mettre à jour uniquement le montant restant
.\ecrm.bat contract update 42 --remaining-amount 3000

# Mettre à jour plusieurs champs
.\ecrm.bat contract update 42 --amount 5000 --remaining-amount 3000 --signed
```

### Supprimer un Contrat
```bash
.\ecrm.bat contract delete-contract ID
```
**Description** : Supprime un contrat
**Arguments** :
- `ID` : L'identifiant du contrat à supprimer
**Options** :
- `--confirm` : Confirme la suppression sans demander de confirmation interactive
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat contract delete-contract 42 --confirm
```

### Contrats Non Signés
```bash
.\ecrm.bat contract non-signes
```
**Description** : Affiche la liste des contrats non signés
**Options** : Aucune
**Permissions** : Tous les départements

**Exemple** :
```bash
.\ecrm.bat contract non-signes
```

### Mes Contrats
```bash
.\ecrm.bat contract my-contracts
```
**Description** : Affiche la liste des contrats des clients dont je suis le commercial
**Options** : Aucune
**Permissions** : Département commercial uniquement

**Exemple** :
```bash
.\ecrm.bat contract my-contracts
```

## Gestion des Événements

### Créer un Événement
```bash
.\ecrm.bat event create
```
**Description** : Création d'un nouvel événement
**Options** :
- `--contract` ou `-c` : ID du contrat associé (requis)
- `--name` ou `-n` : Nom de l'événement (requis)
- `--start-date` ou `-s` : Date et heure de début (requis, format : YYYY-MM-DD HH:MM)
- `--end-date` ou `-e` : Date et heure de fin (requis, format : YYYY-MM-DD HH:MM)
- `--location` ou `-l` : Lieu de l'événement (requis)
- `--attendees` ou `-a` : Nombre de participants (requis)
- `--notes` : Notes supplémentaires (optionnel)
**Permissions** : Département commercial uniquement

**Exemple** :
```bash
.\ecrm.bat event create --contract 1 --name "Conférence 2024" --start-date "2024-06-01 09:00" --end-date "2024-06-02 18:00" --location "Paris" --attendees 100
```

### Lister les Événements
```bash
.\ecrm.bat event list-events
```
**Description** : Affiche la liste de tous les événements avec pagination
**Options** :
- `--page` : Numéro de page à afficher (défaut: 1)
- `--page-size` : Nombre d'événements par page (défaut: 10)
**Permissions** : Tous les départements
**Pagination** : 
- Les résultats sont paginés par défaut (10 éléments par page)
- Le nombre total d'événements est affiché
- Navigation possible entre les pages avec l'option --page

**Exemple** :
```bash
# Afficher la première page avec 10 événements par page (par défaut)
.\ecrm.bat event list-events

# Afficher la deuxième page avec 5 événements par page
.\ecrm.bat event list-events --page 2 --page-size 5
```

### Afficher un Événement
```bash
.\ecrm.bat event get-event ID
```
**Description** : Affiche les détails d'un événement spécifique
**Arguments** :
- `ID` : L'identifiant de l'événement à afficher
**Permissions** : Tous les départements

**Exemple** :
```bash
.\ecrm.bat event get-event 42
```

### Mettre à jour un Événement
```bash
.\ecrm.bat event update ID
```
**Description** : Met à jour les informations d'un événement
**Arguments** :
- `ID` : L'identifiant de l'événement à mettre à jour
**Options** :
- `--name` ou `-n` : Nouveau nom de l'événement
- `--start-date` ou `-s` : Nouvelle date et heure de début (format : YYYY-MM-DD HH:MM)
- `--end-date` ou `-e` : Nouvelle date et heure de fin (format : YYYY-MM-DD HH:MM)
- `--location` ou `-l` : Nouveau lieu de l'événement
- `--attendees` ou `-a` : Nouveau nombre de participants
- `--notes` : Nouvelles notes supplémentaires
**Permissions** : Département commercial (créateur) et support (pour les événements assignés)

**Exemple** :
```bash
.\ecrm.bat event update 42 --location "Lyon" --notes "Changement de lieu"
```

### Mettre à jour les Notes d'un Événement
```bash
.\ecrm.bat event update-notes ID NOTES
```
**Description** : Met à jour les notes d'un événement (pour le support)
**Arguments** :
- `ID` : L'identifiant de l'événement à mettre à jour
- `NOTES` : Les nouvelles notes
**Permissions** : Département support (uniquement pour ses événements assignés)

**Exemple** :
```bash
.\ecrm.bat event update-notes 42 "Prévoir 20 places de parking supplémentaires"
```

### Assigner un Support
```bash
.\ecrm.bat event assign-support ID SUPPORT_ID
```
**Description** : Assigne un contact support à un événement
**Arguments** :
- `ID` : L'identifiant de l'événement
- `SUPPORT_ID` : L'identifiant de l'utilisateur du département support
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat event assign-support 42 3
```

### Supprimer un Événement
```bash
.\ecrm.bat event delete-event ID
```
**Description** : Supprime un événement
**Arguments** :
- `ID` : L'identifiant de l'événement à supprimer
**Options** :
- `--confirm` : Confirme la suppression sans demander de confirmation interactive
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat event delete-event 42 --confirm
```

### Mes Événements
```bash
.\ecrm.bat event my-events
```
**Description** : Affiche la liste des événements assignés à l'utilisateur connecté (support)
**Options** : Aucune
**Permissions** : Département support uniquement

**Exemple** :
```bash
.\ecrm.bat event my-events
```

### Événements Sans Support
```bash
.\ecrm.bat event without-support
```
**Description** : Affiche la liste des événements sans contact support assigné
**Options** : Aucune
**Permissions** : Département gestion uniquement

**Exemple** :
```bash
.\ecrm.bat event without-support
```

### Événements par Contrat
```bash
.\ecrm.bat event by-contract CONTRACT_ID
```
**Description** : Liste les événements d'un contrat spécifique
**Arguments** :
- `CONTRACT_ID` : L'identifiant du contrat
**Permissions** : Tous les départements

**Exemple** :
```bash
.\ecrm.bat event by-contract 42
```

## Authentification

### Connexion
```bash
.\ecrm.bat auth login
```
**Description** : Se connecter à l'application
**Options** : Aucune (demande interactive de l'email et du mot de passe)

**Exemple** :
```bash
.\ecrm.bat auth login
```

### Déconnexion
```bash
.\ecrm.bat auth logout
```
**Description** : Se déconnecter de l'application
**Options** : Aucune

**Exemple** :
```bash
.\ecrm.bat auth logout
```

## Options Globales
Toutes les commandes acceptent les options globales suivantes :
- `--help` : Affiche l'aide de la commande

## Notes
- Les commandes nécessitent une authentification préalable via la commande `auth login`
- Les permissions sont vérifiées automatiquement pour chaque commande
- Les dates doivent être fournies au format YYYY-MM-DD HH:MM
- Les montants doivent être fournis en euros (sans symbole)