"""add district column to locations

Revision ID: c738e6d2e546
Revises: 3844ce82841d
Create Date: 2026-09-19 14:53:08.943251
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.utils.district import nearest_district

# revision identifiers, used by Alembic.
revision: str = 'c738e6d2e546'
down_revision: Union[str, Sequence[str], None] = '3844ce82841d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('locations', sa.Column('district', sa.String(), nullable=True))

    # Backfill district for any locations that existed before this column.
    # WAQI gives us no district field, so this uses the same
    # nearest-reference-point approximation as app.utils.district --
    # kept in sync with the seed script so old and new rows agree.
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, ST_Y(geometry) AS lat, ST_X(geometry) AS lng FROM locations")
    ).fetchall()

    for row in rows:
        district = nearest_district(row.lat, row.lng)
        bind.execute(
            sa.text("UPDATE locations SET district = :district WHERE id = :id"),
            {"district": district, "id": row.id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('locations', 'district')
