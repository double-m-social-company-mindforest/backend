"""merge branches

Revision ID: d5b1648cec16
Revises: 48bb5bfb3086, c4ebbb1dc3d0
Create Date: 2025-09-01 10:17:29.602283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5b1648cec16'
down_revision: Union[str, None] = ('48bb5bfb3086', 'c4ebbb1dc3d0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
