"""suppression_champs_redondants_event

Revision ID: 38507fe42c20
Revises: 984fd35abd55
Create Date: 2025-04-11 15:54:53.207932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38507fe42c20'
down_revision: Union[str, None] = '984fd35abd55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Supprime les colonnes redondantes de la table events."""
    # Sauvegarde des données si nécessaire
    op.execute("""
        CREATE TABLE events_backup AS
        SELECT id, name, contract_id, client_id, start_event, end_event,
               location, support_contact_id, attendees, notes
        FROM events;
    """)

    # Suppression des colonnes redondantes
    op.drop_column('events', 'client_name')
    op.drop_column('events', 'client_contact')


def downgrade() -> None:
    """Restaure les colonnes supprimées."""
    # Ajout des colonnes
    op.add_column('events', sa.Column('client_name', sa.String(), nullable=True))
    op.add_column('events', sa.Column('client_contact', sa.String(), nullable=True))

    # Restauration des données depuis la table de sauvegarde
    op.execute("""
        DROP TABLE IF EXISTS events_backup;
    """)
