"""
Integration tests yang membutuhkan PostgreSQL test database.

Jalankan dengan:
docker compose -f docker-compose.test.yml up -d postgres_test
TEST_DATABASE_URL=postgresql://test:test@localhost:5433/pcb_test pytest -m postgres
"""

import uuid

import pytest

from app.models.device import Device, SensorLog


pytestmark = pytest.mark.postgres


def test_postgres_daily_stats_endpoint_handles_date_aggregation(
    postgres_client,
    postgres_admin_headers,
    postgres_device_claimed,
    postgres_sensor_logs,
):
    response = postgres_client.get(
        f"/api/devices/{postgres_device_claimed.id}/stats/daily",
        headers=postgres_admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == str(postgres_device_claimed.id)
    assert data["device_name"] == postgres_device_claimed.name
    assert data["total_days"] == 1
    assert len(data["statistics"]) == 1

    stat = data["statistics"][0]
    assert stat["data_points"] == len(postgres_sensor_logs)
    assert stat["min_temperature"] <= stat["avg_temperature"] <= stat["max_temperature"]
    assert stat["status"] in {"Normal", "Waspada", "Bahaya"}


def test_postgres_delete_device_cascades_sensor_logs(
    postgres_client,
    postgres_db_session,
    postgres_super_admin_headers,
    postgres_device_claimed,
    postgres_sensor_logs,
):
    assert postgres_db_session.query(SensorLog).filter(
        SensorLog.device_id == postgres_device_claimed.id
    ).count() == len(postgres_sensor_logs)

    response = postgres_client.delete(
        f"/api/devices/{postgres_device_claimed.id}",
        headers=postgres_super_admin_headers,
    )

    assert response.status_code == 200
    assert postgres_db_session.query(Device).filter(
        Device.id == postgres_device_claimed.id
    ).first() is None
    assert postgres_db_session.query(SensorLog).filter(
        SensorLog.device_id == postgres_device_claimed.id
    ).count() == 0


def test_postgres_claim_device_with_uuid_primary_key(
    postgres_client,
    postgres_db_session,
    postgres_admin_headers,
    postgres_admin_user,
):
    device = Device(
        id=uuid.uuid4(),
        mac_address="33:44:55:66:77:88",
        name=None,
        user_id=None,
    )
    postgres_db_session.add(device)
    postgres_db_session.commit()
    postgres_db_session.refresh(device)

    response = postgres_client.post(
        "/api/devices/claim",
        json={"mac_address": device.mac_address, "name": "Kandang Claim PostgreSQL"},
        headers=postgres_admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(device.id)
    assert data["user_id"] == str(postgres_admin_user.id)
    assert data["name"] == "Kandang Claim PostgreSQL"
