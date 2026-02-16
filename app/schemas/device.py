from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, computed_field
from typing import Optional
from uuid import UUID


class DeviceClaim(BaseModel):
    """Schema untuk mengklaim device baru via QR scan"""
    mac_address: str
    name: str  # Nama kandang yang diberikan user


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
    # Contoh: "lampu_utama", "kipas_angin", "pompa_air", "pakan_otomatis"
    component: str 
    
    # Mau diapain?
    # True = NYALA (ON), False = MATI (OFF)
    state: bool
