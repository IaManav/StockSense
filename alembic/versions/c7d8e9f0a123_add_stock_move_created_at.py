"""add timestamps to stock moves

Revision ID: c7d8e9f0a123
Revises: b5e6f7a8c901
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7d8e9f0a123"
down_revision: Union[str, None] = "b5e6f7a8c901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stock_moves", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()))
    op.alter_column("stock_moves", "created_at", nullable=False)


def downgrade() -> None:
    op.drop_column("stock_moves", "created_at")
