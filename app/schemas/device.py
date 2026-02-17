from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, computed_field, field_validator
from typing import Optional, Literal
from uuid import UUID
import re


class DeviceClaim(BaseModel):
    """Schema untuk mengklaim device baru via QR scan"""
    mac_address: str
    name: str  # Nama kandang yang diberikan user

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        """Validasi format MAC address (XX:XX:XX:XX:XX:XX)"""
        pattern = r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
        if not re.match(pattern, v):
            raise ValueError("Format MAC address tidak valid! Gunakan format XX:XX:XX:XX:XX:XX")
        return v.upper()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validasi panjang nama device"""
        if len(v.strip()) < 1:
            raise ValueError("Nama device tidak boleh kosong")
        if len(v) > 100:
            raise ValueError("Nama device maksimal 100 karakter")
        return v.strip()


class DeviceResponse(BaseModel):
    """Schema response data device"""
    id: UUID
    mac_address: str
    name: str
    user_id: Optional[UUID] = None
    last_heartbeat: Optional[datetime] = None
    
    @computed_field
    def is_online(self) -> bool:
        # Kalau belum pernah kirim data, anggap OFFLINE
        if self.last_heartbeat is None:
            return False
        
        # Ambil waktu sekarang (UTC biar aman)
        now = datetime.now(timezone.utc)
        
        # Hitung selisih waktu
        # Handle both timezone-aware and naive datetimes
        last_hb = self.last_heartbeat
        if last_hb.tzinfo is None:
            # If naive, assume UTC
            last_hb = last_hb.replace(tzinfo=timezone.utc)
        
        diff = now - last_hb
        
        # Kalau selisih kurang dari 5 menit (300 detik) -> ONLINE 🟢
        # Kalau lebih -> OFFLINE 🔴
        return diff < timedelta(minutes=5)

    class Config:
        from_attributes = True


class DeviceUpdate(BaseModel):
    """Schema untuk update data device"""
    name: Optional[str] = None


class DeviceControl(BaseModel):
    # Komponen apa yang mau dikontrol?
    # Hanya komponen yang valid yang diterima
    component: Literal["kipas", "lampu", "pompa", "pakan_otomatis"]
    
    # Mau diapain?
    # True = NYALA (ON), False = MATI (OFF)
    state: bool
