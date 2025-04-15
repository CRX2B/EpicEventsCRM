import os

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from sqlalchemy.orm import Session

from epiceventsCRM.database import SessionLocal, engine
from epiceventsCRM.models.models import Base, Department, User
from epiceventsCRM.utils.auth import hash_password

# Chargement des variables d'environnement
load_dotenv()

# Création d'une console Rich pour l'affichage
console = Console()


def create_departments(db: Session) -> dict:
    """
    Crée les départements dans la base de données.

    Args:
        db (Session): La session de base de données

    Returns:
        dict: Dictionnaire des départements créés
    """
    # Vérification des départements existants
    existing_departments = db.query(Department).all()
    dept_map = {dept.departement_name: dept for dept in existing_departments}

    # Départements à créer
    departments = {
        "commercial": dept_map.get("commercial"),
        "support": dept_map.get("support"),
        "gestion": dept_map.get("gestion"),
    }

    # Création des départements manquants
    for name, dept in departments.items():
        if dept is None:
            new_dept = Department(departement_name=name)
            db.add(new_dept)
            departments[name] = new_dept
            console.print(f"[green]Département '{name}' créé.[/green]")
        else:
            console.print(f"[yellow]Département '{name}' existe déjà.[/yellow]")

    db.commit()
    return departments


def create_admin_user(db: Session, departments: dict) -> None:
    """
    Crée un utilisateur administrateur avec le rôle gestion.

    Args:
        db (Session): La session de base de données
        departments (dict): Dictionnaire des départements
    """
    # Récupération des identifiants administrateur depuis les variables d'environnement
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
    admin_fullname = os.getenv("ADMIN_FULLNAME", "Administrateur")

    # Affichage d'un avertissement si les valeurs par défaut sont utilisées
    if admin_email == "admin@example.com" or admin_password == "changeme":
        console.print(
            Panel.fit(
                "[bold yellow]AVERTISSEMENT: Variables d'environnement ADMIN_EMAIL ou ADMIN_PASSWORD non définies.\n"
                "Utilisation des valeurs par défaut. Créez un fichier .env avec vos propres valeurs.[/bold yellow]",
                border_style="yellow",
            )
        )

    # Vérification si un utilisateur avec ce courriel existe déjà
    existing_user = db.query(User).filter(User.email == admin_email).first()

    if existing_user:
        console.print(f"[yellow]L'utilisateur administrateur ({admin_email}) existe déjà.[/yellow]")
        return

    # Création de l'utilisateur administrateur
    hashed_password = hash_password(admin_password)

    admin_user = User(
        fullname=admin_fullname,
        email=admin_email,
        password=hashed_password,
        departement_id=departments["gestion"].id,
    )

    db.add(admin_user)
    db.commit()
    console.print(f"[green]Utilisateur administrateur créé: {admin_email}[/green]")

    # Avertissement si la variable d'environnement n'est pas définie
    if admin_password == "changeme":
        console.print(
            Panel.fit(
                "[bold red]ATTENTION: Changez le mot de passe administrateur en définissant ADMIN_PASSWORD dans le fichier .env![/bold red]",
                border_style="red",
            )
        )


@click.command()
def init_db():
    """Initialise la base de données avec les tables, départements et un utilisateur administrateur."""
    # Création des tables
    Base.metadata.create_all(bind=engine)
    console.print("[green]Tables créées.[/green]")

    # Création des départements et de l'utilisateur administrateur
    with SessionLocal() as db:
        departments = create_departments(db)
        create_admin_user(db, departments)

    console.print(
        Panel.fit(
            "[bold green]Initialisation de la base de données terminée.[/bold green]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    init_db()
