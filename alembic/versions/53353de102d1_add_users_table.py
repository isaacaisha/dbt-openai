"""add users table

Revision ID: 53353de102d1
Revises: e01aa9ca49ad
Create Date: 2024-02-18 18:58:05.038755

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53353de102d1'
down_revision = 'e01aa9ca49ad'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing "users" table if it exists
    op.drop_table("users")

    # Create the "users" table
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
                    sa.Column('name', sa.String(255), nullable=False),
                    sa.Column('email', sa.String(255), nullable=False, unique=True),
                    sa.Column('password', sa.String(255), nullable=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.func.now(), nullable=False)
                    )


def downgrade():
    op.drop_table('users')
