from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from uuid import UUID


class UpdateUserName(BaseModel):
    """Schema untuk update nama user"""
    full_name: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Nama tidak boleh kosong")
        if len(v) > 100:
            raise ValueError("Nama maksimal 100 karakter")
        return v


class UserResponse(BaseModel):
    """Schema response data user"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None
    provider: str
    is_active: bool
    role: str  # "admin" atau "user"

    class Config:
        from_attributes = True


class UpdateUserRole(BaseModel):
    """Schema untuk mengubah role user (khusus admin)"""
    role: Literal["admin", "user"]
