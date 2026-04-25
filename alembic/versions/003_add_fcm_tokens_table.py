"""add fcm_tokens table

Revision ID: 003_fcm_tokens
Revises: 002_role_hierarchy
Create Date: 2026-04-25

Menambahkan tabel fcm_tokens untuk menyimpan Firebase Cloud Messaging token
per user. Digunakan untuk push notification saat alert terpicu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = '003_fcm_tokens'
down_revision: Union[str, None] = '002_role_hierarchy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'fcm_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token', sa.String(), nullable=False, unique=True),
        sa.Column('device_info', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('fcm_tokens')
