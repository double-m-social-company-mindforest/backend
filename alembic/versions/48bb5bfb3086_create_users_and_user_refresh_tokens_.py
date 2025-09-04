"""create users and user_refresh_tokens tables

Revision ID: 48bb5bfb3086
Revises: 702ae99e0e36
Create Date: 2025-01-01 13:55:17.520596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48bb5bfb3086'
down_revision: Union[str, None] = 'e9bd0ff9b049'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nickname', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nickname')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_nickname'), 'users', ['nickname'], unique=True)

    # Create user_refresh_tokens table
    op.create_table('user_refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_refresh_tokens_id'), 'user_refresh_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_user_refresh_tokens_token_hash'), 'user_refresh_tokens', ['token_hash'], unique=False)
    op.create_index(op.f('ix_user_refresh_tokens_user_id'), 'user_refresh_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop user_refresh_tokens table
    op.drop_index(op.f('ix_user_refresh_tokens_user_id'), table_name='user_refresh_tokens')
    op.drop_index(op.f('ix_user_refresh_tokens_token_hash'), table_name='user_refresh_tokens')
    op.drop_index(op.f('ix_user_refresh_tokens_id'), table_name='user_refresh_tokens')
    op.drop_table('user_refresh_tokens')
    
    # Drop users table
    op.drop_index(op.f('ix_users_nickname'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')