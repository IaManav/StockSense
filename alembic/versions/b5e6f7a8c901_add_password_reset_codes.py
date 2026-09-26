"""add password reset codes

Revision ID: b5e6f7a8c901
Revises: 9d9a5d2c7f01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5e6f7a8c901"
down_revision: Union[str, None] = "9d9a5d2c7f01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_password_reset_codes_email", "password_reset_codes", ["email"])


def downgrade() -> None:
    op.drop_index("ix_password_reset_codes_email", table_name="password_reset_codes")
    op.drop_table("password_reset_codes")
