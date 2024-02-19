"""create memories table

Revision ID: d8f4f8e7ace5
Revises: 
Create Date: 2024-02-18 17:43:16.582484

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f4f8e7ace5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop the existing "memories" table if it exists
    op.drop_table("memories")

    # Create the "memories" table
    op.create_table('memories',
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
                    sa.Column('user_name', sa.String(55), nullable=False),
                    sa.Column('user_message', sa.Text(), nullable=False),
                    sa.Column('llm_response', sa.Text(), nullable=False),
                    sa.Column('conversations_summary', sa.Text(), nullable=False),
                    sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                              server_default=sa.text("now()"), nullable=False),
                    # Optional liked column
                    sa.Column('liked', sa.String(), nullable=False),
                    sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
                    )
    pass


def downgrade():
    op.drop_table('memories')
    pass
