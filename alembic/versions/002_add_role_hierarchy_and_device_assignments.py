"""add role hierarchy and device assignments

Revision ID: 002_role_hierarchy
Revises: 001_add_role
Create Date: 2026-04-24

Menambahkan:
1. Role baru: super_admin, operator, viewer (role column sudah ada, hanya update values)
2. Tabel device_assignments untuk assign user ke device tertentu
3. Migrasi: user dengan INITIAL_ADMIN_EMAIL di-promote ke super_admin
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = '002_role_hierarchy'
down_revision: Union[str, None] = '001_add_role'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Buat tabel device_assignments
    op.create_table(
        'device_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('assigned_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('device_id', 'user_id', name='uq_device_user_assignment'),
    )

    # 2. Promote user admin yang ada menjadi super_admin
    #    (user pertama dengan role 'admin' yang cocok dengan INITIAL_ADMIN_EMAIL)
    #    Ini dilakukan di app/main.py saat startup, bukan di migration.
    #    Migration hanya membuat tabel — data migration dilakukan oleh aplikasi.


def downgrade() -> None:
    op.drop_table('device_assignments')
