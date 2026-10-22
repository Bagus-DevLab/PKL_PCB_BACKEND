"""add role column to users table

Revision ID: 001_add_role
Revises: 000_initial_schema
Create Date: 2026-04-24

Menambahkan kolom 'role' ke tabel users.
Default value 'user' untuk semua user yang sudah ada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_role'
down_revision: Union[str, None] = '000_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tambah kolom role dengan default 'user'
    # server_default memastikan semua row yang sudah ada mendapat value 'user'
    op.add_column(
        'users',
        sa.Column('role', sa.String(), nullable=False, server_default='user')
    )


def downgrade() -> None:
    op.drop_column('users', 'role')
