from pydantic import BaseModel
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
