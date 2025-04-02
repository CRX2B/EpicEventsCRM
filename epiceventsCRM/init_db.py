import click
from sqlalchemy.orm import Session
from epiceventsCRM.models.models import Department, User
from epiceventsCRM.database import engine, get_session, SessionLocal
from epiceventsCRM.utils.auth import hash_password
from epiceventsCRM.models.models import Base


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
        "gestion": dept_map.get("gestion")
    }
    
    # Création des départements manquants
    for name, dept in departments.items():
        if dept is None:
            new_dept = Department(departement_name=name)
            db.add(new_dept)
            departments[name] = new_dept
            print(f"Département '{name}' créé.")
        else:
            print(f"Département '{name}' existe déjà.")
    
    db.commit()
    return departments


def create_admin_user(db: Session, departments: dict) -> None:
    """
    Crée un utilisateur administrateur avec le rôle gestion.
    
    Args:
        db (Session): La session de base de données
        departments (dict): Dictionnaire des départements
    """
    # Vérification si un utilisateur avec ce courriel existe déjà
    email = "admin@epiceventsCRM.com"
    existing_user = db.query(User).filter(User.email == email).first()
    
    if existing_user:
        print(f"L'utilisateur administrateur ({email}) existe déjà.")
        return
    
    # Création de l'utilisateur administrateur
    password = "adminpass"  # À changer en production
    hashed_password = hash_password(password)
    
    admin_user = User(
        fullname="Administrateur",
        email=email,
        password=hashed_password,
        departement_id=departments["gestion"].id
    )
    
    db.add(admin_user)
    db.commit()
    print(f"Utilisateur administrateur créé: {email} (mot de passe: {password})")
    print("ATTENTION: Changez ce mot de passe en production!")


@click.command()
def init_db():
    """Initialise la base de données avec les tables, départements et un utilisateur administrateur."""
    # Création des tables
    Base.metadata.create_all(bind=engine)
    print("Tables créées.")
    
    # Création des départements et de l'utilisateur administrateur
    with SessionLocal() as db:
        departments = create_departments(db)
        create_admin_user(db, departments)
    
    print("Initialisation de la base de données terminée.")


if __name__ == "__main__":
    init_db() 