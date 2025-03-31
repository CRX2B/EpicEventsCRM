"""suppression_colonne_role

Revision ID: 218b4db7b167
Revises: ffd1e9b8a218
Create Date: 2025-03-27 12:02:54.895115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '218b4db7b167'
down_revision: Union[str, None] = 'ffd1e9b8a218'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Suppression de la colonne role
    op.drop_column('users', 'role')


def downgrade() -> None:
    # Recréation de la colonne role
    op.add_column('users', sa.Column('role', sa.String(), nullable=True))
