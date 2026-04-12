from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    """Base schema untuk User"""
    email: EmailStr
    full_name: str  # Ubah jadi wajib (hilangkan Optional) agar sesuai dengan database


class UserCreate(UserBase):
    """Schema request untuk form Register manual"""
    password: str  # Tambahan password khusus untuk register


class UserResponse(UserBase):
    """Schema response data user (tidak akan menampilkan password)"""
    id: UUID
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