"""suppression_colonne_role_force

Revision ID: 2280a5feb35f
Revises: 218b4db7b167
Create Date: 2025-03-31 12:23:53.767722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2280a5feb35f'
down_revision: Union[str, None] = '218b4db7b167'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Suppression forcée de la colonne role avec IF EXISTS
    op.execute('ALTER TABLE users DROP COLUMN IF EXISTS role')


def downgrade() -> None:
    """Downgrade schema."""
    # Recréation de la colonne role
    op.add_column('users', sa.Column('role', sa.String(), nullable=True))
