from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epiceventsCRM.config import DATABASE_URL

# Création de l'engine et de la session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Crée une nouvelle session de base de données (générateur)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_session():
    """Crée et retourne une nouvelle session de base de données."""
    return SessionLocal() 