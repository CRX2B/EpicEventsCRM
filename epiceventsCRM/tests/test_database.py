import pytest
from unittest.mock import patch, MagicMock
import os

from epiceventsCRM.database import get_session


class TestDatabase:
    @patch("epiceventsCRM.database.create_engine")
    @patch("epiceventsCRM.database.sessionmaker")
    def test_get_session(self, mock_sessionmaker, mock_create_engine):
        """Test que la fonction get_session retourne une session."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_session_class = MagicMock()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        with patch("epiceventsCRM.database.SessionLocal", mock_session_class):
            session = get_session()

            assert session == mock_session
            mock_session_class.assert_called_once()
