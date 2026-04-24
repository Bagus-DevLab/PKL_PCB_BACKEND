import uuid
from sqlalchemy import Boolean, Column, String, Float, ForeignKey, DateTime, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mac_address = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    owner = relationship("User", back_populates="devices")
    logs = relationship("SensorLog", back_populates="device")
    assignments = relationship("DeviceAssignment", back_populates="device", cascade="all, delete-orphan")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SensorLog(Base):
    __tablename__ = "sensor_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), index=True)

    temperature = Column(Float)
    humidity = Column(Float)
    ammonia = Column(Float)

    is_alert = Column(Boolean, default=False)
    alert_message = Column(String, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    device = relationship("Device", back_populates="logs")


class DeviceAssignment(Base):
    """
    Tabel assignment: menghubungkan user (operator/viewer) ke device tertentu.
    
    Satu user bisa di-assign ke banyak device.
    Satu device bisa punya banyak user yang di-assign.
    Tapi satu user hanya bisa di-assign 1x per device (UNIQUE constraint).
    """
    __tablename__ = "device_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # "operator" atau "viewer"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    device = relationship("Device", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id])
    assigner = relationship("User", foreign_keys=[assigned_by])

    # Satu user hanya bisa di-assign 1x per device
    __table_args__ = (
        UniqueConstraint("device_id", "user_id", name="uq_device_user_assignment"),
    )
