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
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-client-secret"
os.environ["BASE_URL"] = "http://localhost:8000"
os.environ["MQTT_BROKER"] = "localhost"
os.environ["MQTT_PORT"] = "1883"
os.environ["MQTT_TOPIC"] = "devices/+/data"
os.environ["POSTGRES_USER"] = "test"
os.environ["POSTGRES_PASSWORD"] = "test"
os.environ["POSTGRES_DB"] = "test"
os.environ["ENVIRONMENT"] = "development"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.device import Device, SensorLog
from app.core.security import create_access_token
import app.database as database_module
import app.main as main_module


# Test Database Setup (SQLite in-memory with StaticPool for connection sharing)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Important: reuses same connection
)

# Patch the app's engine to use our test engine
database_module.engine = engine
main_module.engine = engine

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create tables once at module load
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Fixture untuk database session dengan proper cleanup.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Clean up all data after each test
        db.query(SensorLog).delete()
        db.query(Device).delete()
        db.query(User).delete()
        db.commit()
        db.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """
    Fixture untuk TestClient.
    Override database dependency dengan test database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> User:
    """
    Fixture untuk membuat user test di database.
    """
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        full_name="Test User",
        picture="https://example.com/picture.jpg",
        provider="google",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user) -> str:
    """
    Fixture untuk membuat JWT token dari test user.
    """
    return create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )


@pytest.fixture
def auth_headers(test_user_token) -> dict:
    """
    Fixture untuk headers dengan Bearer token.
    """
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def test_device_unclaimed(db_session) -> Device:
    """
    Fixture untuk membuat device BELUM diklaim (dari pabrik).
    """
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
def test_device_claimed(db_session, test_user) -> Device:
    """
    Fixture untuk membuat device SUDAH diklaim user.
    """
    device = Device(
        id=uuid.uuid4(),
        mac_address="11:22:33:44:55:66",
        name="Kandang Ayam Utama",
        user_id=test_user.id,
        last_heartbeat=datetime.now(timezone.utc)
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def test_sensor_logs(db_session, test_device_claimed) -> list:
    """
    Fixture untuk membuat sample sensor logs.
    """
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
    
    # Tambah 1 alert log
    alert_log = SensorLog(
        device_id=test_device_claimed.id,
        temperature=40.0,  # Suhu bahaya
        humidity=80.0,
        ammonia=25.0,  # Amonia bahaya
        is_alert=True,
        alert_message="Suhu terlalu tinggi!"
    )
    db_session.add(alert_log)
    logs.append(alert_log)
    
    db_session.commit()
    return logs
