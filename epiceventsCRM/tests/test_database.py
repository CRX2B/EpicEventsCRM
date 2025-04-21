import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class TestDatabaseConnection:
    """Tests basiques de connexion à la base de données de test"""

    def test_connection(self, engine):
        """Teste si la connexion à la base de données peut être établie."""
        try:
            connection = engine.connect()
            assert connection is not None
            connection.close()
        except Exception as e:
            pytest.fail(f"Échec de la connexion à la base de données de test: {e}")

    def test_session_creation(self, db_session):
        """Teste si une session peut être créée."""
        assert db_session is not None
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        db_session.close()
