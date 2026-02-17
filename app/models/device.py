import uuid
from sqlalchemy import Boolean, Column, String, Float, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # KTP Alat (MAC Address). Wajib Unik!
    mac_address = Column(String, unique=True, index=True, nullable=False)
    
    # Nama Kandang (Bisa diubah User setelah klaim)
    name = Column(String, nullable=True)
    
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    owner = relationship("User", back_populates="devices")
    logs = relationship("SensorLog", back_populates="device")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SensorLog(Base):
    __tablename__ = "sensor_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), index=True)
    
    temperature = Column(Float)
    humidity = Column(Float)
    ammonia = Column(Float)

    is_alert = Column(Boolean, default=False) # True kalau suhu/amonia kacau
    alert_message = Column(String, nullable=True) # Pesan bahayanya ap
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    device = relationship("Device", back_populates="logs")