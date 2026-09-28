"""add role column to users

Revision ID: d4f7a2c9b1e3
Revises: c738e6d2e546
Create Date: 2026-09-22 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4f7a2c9b1e3'
down_revision: Union[str, Sequence[str], None] = 'c738e6d2e546'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Day 7: guest/registered/admin roles. server_default='registered' so
    every existing row gets a valid role retroactively -- no user is left
    with an unset role after this migration runs.
    """
    op.add_column(
        'users',
        sa.Column('role', sa.String(), nullable=False, server_default='registered'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')