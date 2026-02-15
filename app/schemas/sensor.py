from pydantic import BaseModel
from datetime import datetime


class LogResponse(BaseModel):
    """Schema response untuk data sensor log (grafik)"""
    id: int
    temperature: float
    humidity: float
    ammonia: float
    is_alert: bool # Tambahkan ini
    alert_message: Optional[str] # Tambahkan ini
    timestamp: datetime
    
    class Config:
        from_attributes = True


class LogCreate(BaseModel):
    """Schema untuk membuat sensor log baru (internal use)"""
    temperature: float
    humidity: float
    ammonia: float
