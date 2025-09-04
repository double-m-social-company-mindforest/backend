"""create user_curriculum_sessions table

Revision ID: 38b5dc7d6dda
Revises: d5b1648cec16
Create Date: 2025-01-01 14:35:55.857086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '38b5dc7d6dda'
down_revision: Union[str, None] = 'd5b1648cec16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_curriculum_sessions table
    op.create_table('user_curriculum_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_number', sa.Integer(), nullable=False),
        sa.Column('session_data', postgresql.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='not_started'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'session_number', name='uq_user_session'),
        sa.CheckConstraint('session_number >= 1 AND session_number <= 8', name='check_session_number')
    )
    op.create_index(op.f('ix_user_curriculum_sessions_id'), 'user_curriculum_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_curriculum_sessions_user_id'), 'user_curriculum_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_curriculum_sessions_session_number'), 'user_curriculum_sessions', ['session_number'], unique=False)
    op.create_index(op.f('ix_user_curriculum_sessions_status'), 'user_curriculum_sessions', ['status'], unique=False)


def downgrade() -> None:
    # Drop user_curriculum_sessions table
    op.drop_index(op.f('ix_user_curriculum_sessions_status'), table_name='user_curriculum_sessions')
    op.drop_index(op.f('ix_user_curriculum_sessions_session_number'), table_name='user_curriculum_sessions')
    op.drop_index(op.f('ix_user_curriculum_sessions_user_id'), table_name='user_curriculum_sessions')
    op.drop_index(op.f('ix_user_curriculum_sessions_id'), table_name='user_curriculum_sessions')
    op.drop_table('user_curriculum_sessions')