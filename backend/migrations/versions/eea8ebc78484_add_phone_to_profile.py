"""add_phone_to_profile

Revision ID: eea8ebc78484
Revises: f6f414d8d1e5
Create Date: 2026-01-27 12:18:57.322626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eea8ebc78484'
down_revision: Union[str, None] = 'f6f414d8d1e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_profiles', sa.Column('phone', sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column('user_profiles', 'phone')
