"""add composite index on sensor_logs (device_id, timestamp DESC)

Revision ID: 005_composite_index
Revises: 004_cascade_sensor_log
Create Date: 2026-04-26

Adds a composite index for the most common query pattern:
  WHERE device_id = ? ORDER BY timestamp DESC

This eliminates in-memory sorts on the sensor_logs table,
which can have hundreds of thousands of rows per device.

Safe for production — CREATE INDEX does not lock the table
for reads/writes in PostgreSQL (it only blocks other DDL).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '005_composite_index'
down_revision: Union[str, None] = '004_cascade_sensor_log'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_sensor_logs_device_timestamp",
        "sensor_logs",
        ["device_id", sa.text("timestamp DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_logs_device_timestamp", table_name="sensor_logs")
