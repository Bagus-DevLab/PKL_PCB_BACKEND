"""add light_level column to sensor_logs

Revision ID: 006_light_level
Revises: 005_composite_index
Create Date: 2026-04-27

Adds an optional light_level column (Integer, nullable) to sensor_logs.
Stores LDR reading from ESP32: 0 = gelap, 1 = terang.
Nullable so existing rows are unaffected (default NULL).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '006_light_level'
down_revision: Union[str, None] = '005_composite_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sensor_logs', sa.Column('light_level', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('sensor_logs', 'light_level')
