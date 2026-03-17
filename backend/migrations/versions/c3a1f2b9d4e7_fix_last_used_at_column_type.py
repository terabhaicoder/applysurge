"""fix_last_used_at_column_type

Revision ID: c3a1f2b9d4e7
Revises: eea8ebc78484
Create Date: 2026-02-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a1f2b9d4e7'
down_revision: Union[str, None] = 'eea8ebc78484'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix last_used_at column type from String(50) to DateTime(timezone=True)
    # The initial migration incorrectly created this as String
    op.alter_column(
        'email_templates',
        'last_used_at',
        existing_type=sa.String(length=50),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using='last_used_at::timestamp with time zone',
    )


def downgrade() -> None:
    op.alter_column(
        'email_templates',
        'last_used_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.String(length=50),
        existing_nullable=True,
    )
