from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# --- DEVICE SCHEMAS ---

# Data yang dikirim User saat nge-scan QR
class DeviceClaim(BaseModel):
    mac_address: str
    name: str # User namain kandangnya sendiri

# Data Device yang dikirim balik ke HP
class DeviceResponse(BaseModel):
    id: UUID
    mac_address: str
    name: str
    user_id: Optional[UUID] = None

    class Config:
        from_attributes = True

# --- LOG SCHEMAS (Buat Grafik) ---

class LogResponse(BaseModel):
    id: int
    temperature: float
    humidity: float
    ammonia: float
    timestamp: datetime

    class Config:
        from_attributes = True