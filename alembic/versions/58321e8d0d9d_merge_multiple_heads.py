"""merge multiple heads

Revision ID: 58321e8d0d9d
Revises: 3dee629b7f69, c7d8e9f0a123
Create Date: 2026-09-26 15:51:42.070590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58321e8d0d9d'
down_revision: Union[str, None] = ('3dee629b7f69', 'c7d8e9f0a123')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
