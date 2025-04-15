import os

import psycopg
from dotenv import load_dotenv


def setup_test_database():
    """Crée la base de données de test si elle n'existe pas."""
    load_dotenv(".env.test")

    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

    conn = psycopg.connect(
        dbname="postgres",
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone() is not None

        if not exists:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE {db_name}")
            print(f"Base de données {db_name} créée avec succès.")
        else:
            print(f"La base de données {db_name} existe déjà.")

    finally:
        conn.close()


if __name__ == "__main__":
    setup_test_database()
