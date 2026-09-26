"""make location names and shortcut codes unique per warehouse

Revision ID: d8e9f0a1b234
Revises: c7d8e9f0a123
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d8e9f0a1b234"
down_revision: Union[str, None] = "c7d8e9f0a123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_location_warehouse_name", "locations", ["warehouse_id", "name"])
    op.create_unique_constraint("uq_location_warehouse_short_code", "locations", ["warehouse_id", "short_code"])


def downgrade() -> None:
    op.drop_constraint("uq_location_warehouse_short_code", "locations", type_="unique")
    op.drop_constraint("uq_location_warehouse_name", "locations", type_="unique")
