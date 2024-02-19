"""add api_memories

Revision ID: 9316a4e2e9d8
Revises: 53353de102d1
Create Date: 2024-02-18 20:10:08.671572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9316a4e2e9d8'
down_revision: Union[str, None] = '53353de102d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create api_users table
    op.create_table('api_users',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False, autoincrement=True),
                    sa.Column('email', sa.String(), nullable=False, unique=True),
                    sa.Column('password', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
                    )

    # Create api_memories table
    op.create_table('api_memories',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False, autoincrement=True),
                    sa.Column('user_message', sa.String(), nullable=False),
                    sa.Column('llm_response', sa.String(), nullable=False),
                    sa.Column('conversations_summary', sa.String(), nullable=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
                    sa.Column('owner_id', sa.Integer(), sa.ForeignKey('api_users.id', ondelete='CASCADE'), nullable=False)
                    )

    # Create api_votes table
    op.create_table('api_votes',
                    sa.Column('user_id', sa.Integer(), sa.ForeignKey('api_users.id', ondelete='CASCADE'), primary_key=True),
                    sa.Column('post_id', sa.Integer(), sa.ForeignKey('api_memories.id', ondelete='CASCADE'), primary_key=True),
                    sa.Column('memory_id', sa.Integer(), sa.ForeignKey('api_memories.id', ondelete='CASCADE')),
                    sa.PrimaryKeyConstraint('user_id', 'post_id')
                    )

    # Create relationships
    op.create_foreign_key('fk_api_memories_owner_id_api_users', 'api_memories', 'api_users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_api_memories_owner_id', 'api_memories', ['owner_id'], unique=False)
    op.create_foreign_key('fk_api_votes_memory_id_api_memories', 'api_votes', 'api_memories', ['memory_id'], ['id'], ondelete='CASCADE')

    # Add back reference for memories relationship in api_users table
    op.add_column('api_users', sa.Column('memories', sa.Integer(), sa.ForeignKey('api_memories.id', ondelete='CASCADE')))


def downgrade() -> None:
    # Remove back reference for memories relationship in api_users table
    op.drop_column('api_users', 'memories')

    # Drop api_votes table
    op.drop_table('api_votes')

    # Drop api_memories table
    op.drop_table('api_memories')

    # Drop api_users table
    op.drop_table('api_users')
