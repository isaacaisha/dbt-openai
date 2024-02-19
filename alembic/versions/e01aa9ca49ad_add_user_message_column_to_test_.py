"""add user_message column to test_memories tables

Revision ID: e01aa9ca49ad
Revises: 3a8bfb281e62
Create Date: 2024-02-18 16:02:34.968673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e01aa9ca49ad'
down_revision: Union[str, None] = '3a8bfb281e62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("test_memories", sa.Column("user_message", sa.String(), nullable=False))
    pass


def downgrade():
    op.drop_colum("test_memories", "user_message")
    pass
