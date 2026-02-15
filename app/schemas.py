from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# --- SCHEMA BUAT DEVICE ---

# Ini data yang User KIRIM saat mau klaim alat
class DeviceCreate(BaseModel):
    mac_address: str  # Wajib ada
    name: str         # Wajib ada (misal: "Kandang 1")

# Ini data yang Server BALIKIN ke User
class DeviceResponse(DeviceCreate):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True  # Biar bisa baca data langsung dari SQLAlchemy