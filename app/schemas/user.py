from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID


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
