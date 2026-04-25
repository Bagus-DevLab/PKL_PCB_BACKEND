"""add cascade to sensor_log device_id foreign key

Revision ID: 004_cascade_sensor_log
Revises: 003_fcm_tokens
Create Date: 2026-04-25

Adds ON DELETE CASCADE to sensor_logs.device_id foreign key.
This ensures PostgreSQL automatically deletes sensor logs when a device
is deleted, preventing IntegrityError if the MQTT worker inserts a log
during the deletion window.

Safe for existing data — only modifies the FK constraint definition,
does not delete or modify any rows.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '004_cascade_sensor_log'
down_revision: Union[str, None] = '003_fcm_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("sensor_logs_device_id_fkey", "sensor_logs", type_="foreignkey")
    op.create_foreign_key(
        "sensor_logs_device_id_fkey",
        "sensor_logs",
        "devices",
        ["device_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("sensor_logs_device_id_fkey", "sensor_logs", type_="foreignkey")
    op.create_foreign_key(
        "sensor_logs_device_id_fkey",
        "sensor_logs",
        "devices",
        ["device_id"],
        ["id"],
    )
