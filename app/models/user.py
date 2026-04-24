import enum
import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship


class UserRole(str, enum.Enum):
    """
    Enum untuk role user di sistem.
    Menggunakan str mixin agar value bisa langsung dibandingkan dengan string.
    """
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    
    # Bikin nullable=True karena user yang daftar via Email/Pass Firebase 
    # kadang nggak langsung punya nama sampai di-set manual.
    full_name = Column(String, nullable=True) 
    picture = Column(String, nullable=True)
    provider = Column(String, default="firebase") 
    is_active = Column(Boolean, default=True)
    
    # Role user: "admin" atau "user". Default "user" untuk semua pendaftar baru.
    role = Column(String, nullable=False, default=UserRole.USER.value)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    devices = relationship("Device", back_populates="owner")