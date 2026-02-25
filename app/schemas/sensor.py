from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LogResponse(BaseModel):
    """Schema response untuk data sensor log (grafik)"""
    id: int
    temperature: float
    humidity: float
    ammonia: float
    is_alert: bool 
    alert_message: Optional[str] 
    timestamp: datetime
    
    class Config:
        from_attributes = True


class LogCreate(BaseModel):
    """Schema untuk membuat sensor log baru (internal use)"""
    temperature: float
    humidity: float
    ammonia: float
