from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    """Base schema untuk User"""
    email: EmailStr
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema response data user"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None
    provider: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema response untuk JWT token"""
    access_token: str
    token_type: str = "bearer"
    user_info: Optional[dict] = None
