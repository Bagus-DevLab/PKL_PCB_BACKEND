"""create the base application schema

Revision ID: 000_initial_schema
Revises:
Create Date: 2026-10-23

The original schema was created by SQLAlchemy create_all() in development.
Production disables create_all(), so this revision creates the tables that
existed before the role and feature migrations were introduced.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "000_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("picture", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("mac_address", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_devices_mac_address", "devices", ["mac_address"], unique=True)
    op.create_index("ix_devices_user_id", "devices", ["user_id"])

    op.create_table(
        "sensor_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Float(), nullable=True),
        sa.Column("ammonia", sa.Float(), nullable=True),
        sa.Column("is_alert", sa.Boolean(), nullable=True),
        sa.Column("alert_message", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sensor_logs_id", "sensor_logs", ["id"])
    op.create_index("ix_sensor_logs_device_id", "sensor_logs", ["device_id"])
    op.create_index("ix_sensor_logs_timestamp", "sensor_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("sensor_logs")
    op.drop_table("devices")
    op.drop_table("users")
