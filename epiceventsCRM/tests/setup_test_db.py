import os
import psycopg
from dotenv import load_dotenv
from sqlalchemy import create_engine
from epiceventsCRM.models.models import Base

# Chargement des variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = "EpicCRM_test"

def setup_test_database():
    """Configure la base de données de test."""
    if not DB_USER or not DB_PASSWORD:
        print("ERREUR : Les variables d'environnement DB_USER et DB_PASSWORD doivent être définies.")
        return

    # Connexion à la base de données postgres
    conn = psycopg.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        autocommit=True
    )
    
    try:
        # Vérification si la base de données existe déjà
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
            exists = cur.fetchone() is not None
            
            if exists:
                print(f"La base de données {DB_NAME} existe.")
                
                # Création des tables dans la base de données de test
                test_db_url = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
                engine = create_engine(test_db_url)
                Base.metadata.create_all(engine)
                print(f"Les tables ont été créées dans la base de données {DB_NAME}.")
            else:
                print(f"ERREUR : La base de données {DB_NAME} n'existe pas.")
                print("Veuillez la créer manuellement avec pgAdmin ou la commande :")
                print(f"psql -U postgres -c \"CREATE DATABASE {DB_NAME};\"")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_test_database() 