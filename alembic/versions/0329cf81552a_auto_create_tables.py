"""auto-create-tables

Revision ID: 0329cf81552a
Revises: 9316a4e2e9d8
Create Date: 2024-02-18 20:53:18.272170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0329cf81552a'
down_revision: Union[str, None] = '9316a4e2e9d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False, autoincrement=True),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('email', sa.String(length=255), nullable=False),
                    sa.Column('password', sa.String(length=255), nullable=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
                    sa.UniqueConstraint('email', name='users_email_key')
                    )

    # Create memories table
    op.create_table('memories',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False, autoincrement=True),
                    sa.Column('user_name', sa.String(length=255), nullable=False),
                    sa.Column('user_message', sa.Text(), nullable=False),
                    sa.Column('llm_response', sa.Text(), nullable=False),
                    sa.Column('conversations_summary', sa.Text(), nullable=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
                    sa.Column('liked', sa.Integer(), nullable=True),
                    sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
                    )

    # ### end Alembic commands ###


def downgrade() -> None:
    # Drop memories table
    op.drop_table('memories')

    # Drop users table
    op.drop_table('users')
