"""add stock transfer tables and category description

Revision ID: 9d9a5d2c7f01
Revises: cef63debf4e3
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d9a5d2c7f01"
down_revision: Union[str, None] = "cef63debf4e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("description", sa.Text(), nullable=True))

    transfer_status = sa.Enum(
        "DRAFT", "READY", "DONE", "CANCELLED", name="transferstatus"
    )
    op.create_table(
        "stock_transfers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(length=50), nullable=False),
        sa.Column("from_location_id", sa.Uuid(), nullable=False),
        sa.Column("to_location_id", sa.Uuid(), nullable=False),
        sa.Column("responsible_id", sa.Uuid(), nullable=False),
        sa.Column("status", transfer_status, nullable=False),
        sa.ForeignKeyConstraint(["from_location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["to_location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["responsible_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
    )
    op.create_table(
        "transfer_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("transfer_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.ForeignKeyConstraint(
            ["transfer_id"], ["stock_transfers.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("transfer_items")
    op.drop_table("stock_transfers")
    op.drop_column("categories", "description")
