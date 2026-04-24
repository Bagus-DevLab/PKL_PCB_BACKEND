"""
Pytest fixtures untuk testing PKL PCB IoT Backend.
Menggunakan SQLite in-memory database untuk isolasi test.
"""

import os
import pytest
import uuid
from datetime import datetime, timezone
from typing import Generator

# Set env variables SEBELUM import app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["MQTT_BROKER"] = "localhost"
os.environ["MQTT_PORT"] = "1883"
os.environ["MQTT_TOPIC"] = "devices/+/data"
os.environ["MQTT_USERNAME"] = ""
os.environ["MQTT_PASSWORD"] = ""
os.environ["POSTGRES_USER"] = "test"
os.environ["POSTGRES_PASSWORD"] = "test"
os.environ["POSTGRES_DB"] = "test"
os.environ["ENVIRONMENT"] = "development"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
os.environ["INITIAL_ADMIN_EMAIL"] = ""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.device import Device, SensorLog, DeviceAssignment
from app.core.security import create_access_token
import app.database as database_module
import app.main as main_module


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

database_module.engine = engine
main_module.engine = engine

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.query(DeviceAssignment).delete()
        db.query(SensorLog).delete()
        db.query(Device).delete()
        db.query(User).delete()
        db.commit()
        db.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==========================================
# USER FIXTURES (5 roles)
# ==========================================

def _create_user(db_session, email, name, role):
    user = User(
        id=uuid.uuid4(),
        email=email,
        full_name=name,
        picture=f"https://example.com/{name.lower().replace(' ', '')}.jpg",
        provider="google",
        is_active=True,
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_token(user):
    return create_access_token(data={"sub": str(user.id), "email": user.email})


def _create_headers(user):
    return {"Authorization": f"Bearer {_create_token(user)}"}


@pytest.fixture
def test_user(db_session) -> User:
    """User default (role: user) — tidak bisa akses device apapun."""
    return _create_user(db_session, "testuser@example.com", "Test User", UserRole.USER.value)


@pytest.fixture
def test_user_token(test_user) -> str:
    return _create_token(test_user)


@pytest.fixture
def auth_headers(test_user_token) -> dict:
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def test_super_admin(db_session) -> User:
    """Super Admin — akses penuh ke seluruh sistem."""
    return _create_user(db_session, "superadmin@example.com", "Super Admin", UserRole.SUPER_ADMIN.value)


@pytest.fixture
def super_admin_headers(test_super_admin) -> dict:
    return _create_headers(test_super_admin)


@pytest.fixture
def test_admin_user(db_session) -> User:
    """Admin (pemilik usaha) — bisa claim device, assign operator/viewer."""
    return _create_user(db_session, "admin@example.com", "Admin User", UserRole.ADMIN.value)


@pytest.fixture
def admin_token(test_admin_user) -> str:
    return _create_token(test_admin_user)


@pytest.fixture
def admin_headers(admin_token) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_operator(db_session) -> User:
    """Operator — bisa lihat + kontrol device yang di-assign."""
    return _create_user(db_session, "operator@example.com", "Operator User", UserRole.OPERATOR.value)


@pytest.fixture
def operator_headers(test_operator) -> dict:
    return _create_headers(test_operator)


@pytest.fixture
def test_viewer(db_session) -> User:
    """Viewer — hanya bisa lihat data device yang di-assign (read-only)."""
    return _create_user(db_session, "viewer@example.com", "Viewer User", UserRole.VIEWER.value)


@pytest.fixture
def viewer_headers(test_viewer) -> dict:
    return _create_headers(test_viewer)


# ==========================================
# DEVICE FIXTURES
# ==========================================

@pytest.fixture
def test_device_unclaimed(db_session) -> Device:
    """Device belum diklaim (dari pabrik)."""
    device = Device(
        id=uuid.uuid4(),
        mac_address="AA:BB:CC:DD:EE:FF",
        name="Stok Pabrik #1",
        user_id=None
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def test_device_claimed(db_session, test_admin_user) -> Device:
    """Device milik admin (sudah diklaim)."""
    device = Device(
        id=uuid.uuid4(),
        mac_address="11:22:33:44:55:66",
        name="Kandang Ayam Utama",
        user_id=test_admin_user.id,
        last_heartbeat=datetime.now(timezone.utc)
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def test_sensor_logs(db_session, test_device_claimed) -> list:
    """Sample sensor logs untuk test_device_claimed."""
    logs = []
    for i in range(5):
        log = SensorLog(
            device_id=test_device_claimed.id,
            temperature=25.0 + i,
            humidity=70.0 + i,
            ammonia=5.0 + i,
            is_alert=False
        )
        db_session.add(log)
        logs.append(log)

    alert_log = SensorLog(
        device_id=test_device_claimed.id,
        temperature=40.0,
        humidity=80.0,
        ammonia=25.0,
        is_alert=True,
        alert_message="Suhu terlalu tinggi!"
    )
    db_session.add(alert_log)
    logs.append(alert_log)

    db_session.commit()
    return logs


@pytest.fixture
def test_device_other_user(db_session) -> Device:
    """Device milik user lain (bukan test_admin_user)."""
    other_admin = _create_user(db_session, "otheradmin@example.com", "Other Admin", UserRole.ADMIN.value)
    device = Device(
        id=uuid.uuid4(),
        mac_address="FF:EE:DD:CC:BB:AA",
        name="Kandang Milik Orang Lain",
        user_id=other_admin.id,
        last_heartbeat=datetime.now(timezone.utc)
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def test_device_claimed_no_logs(db_session, test_admin_user) -> Device:
    """Device milik admin tapi tanpa sensor log."""
    device = Device(
        id=uuid.uuid4(),
        mac_address="99:88:77:66:55:44",
        name="Kandang Kosong",
        user_id=test_admin_user.id,
        last_heartbeat=datetime.now(timezone.utc)
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def test_sensor_logs_old(db_session, test_device_claimed) -> list:
    """Sensor logs dengan timestamp lama (> 90 hari lalu)."""
    from datetime import timedelta

    old_timestamp = datetime.now(timezone.utc) - timedelta(days=180)
    logs = []
    for i in range(3):
        log = SensorLog(
            device_id=test_device_claimed.id,
            temperature=26.0 + i,
            humidity=65.0 + i,
            ammonia=8.0 + i,
            is_alert=False,
            timestamp=old_timestamp + timedelta(hours=i)
        )
        db_session.add(log)
        logs.append(log)

    db_session.commit()
    return logs


# ==========================================
# ASSIGNMENT FIXTURES
# ==========================================

@pytest.fixture
def test_operator_assignment(db_session, test_device_claimed, test_operator, test_admin_user) -> DeviceAssignment:
    """Operator di-assign ke test_device_claimed oleh admin."""
    assignment = DeviceAssignment(
        id=uuid.uuid4(),
        device_id=test_device_claimed.id,
        user_id=test_operator.id,
        assigned_by=test_admin_user.id,
        role=UserRole.OPERATOR.value,
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


@pytest.fixture
def test_viewer_assignment(db_session, test_device_claimed, test_viewer, test_admin_user) -> DeviceAssignment:
    """Viewer di-assign ke test_device_claimed oleh admin."""
    assignment = DeviceAssignment(
        id=uuid.uuid4(),
        device_id=test_device_claimed.id,
        user_id=test_viewer.id,
        assigned_by=test_admin_user.id,
        role=UserRole.VIEWER.value,
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment
