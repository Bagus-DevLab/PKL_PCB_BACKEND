import uuid
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# --- TABEL 1: DAFTAR ALAT (KANDANG) ---
class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # KTP Alat (MAC Address). Wajib Unik!
    # Contoh: "A1:B2:C3:D4:E5:F6"
    mac_address = Column(String, unique=True, index=True, nullable=False)
    
    # Nama Kandang (Misal: "Kandang Belakang")
    name = Column(String, nullable=True)
    
    # Pemilik Alat (Foreign Key ke tabel users)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relasi balik ke User
    owner = relationship("User", back_populates="devices")
    
    # Relasi ke Sensor Log (1 Device punya Banyak Log)
    logs = relationship("SensorLog", back_populates="device")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# --- TABEL 2: RIWAYAT SENSOR (BIG DATA CALON SKRIPSI) ---
class SensorLog(Base):
    __tablename__ = "sensor_logs"

    # Kita pakai Integer Auto Increment aja biar hemat storage dibanding UUID
    id = Column(Integer, primary_key=True, index=True)
    
    # Alat mana yang ngirim?
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"))
    
    # Data Sensor
    temperature = Column(Float) # Suhu
    humidity = Column(Float)    # Kelembapan
    ammonia = Column(Float)     # Gas Amonia (Penting buat ayam!)

    # Waktu pencatatan (Sangat Krusial buat Grafik/Big Data)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relasi balik ke Device
    device = relationship("Device", back_populates="logs")