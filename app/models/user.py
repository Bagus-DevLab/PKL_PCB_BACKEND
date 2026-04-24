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
    Hierarki: super_admin > admin > operator > viewer > user
    
    - super_admin: Mengelola seluruh sistem, register device, manage semua role
    - admin: Pemilik usaha, claim device, assign operator/viewer ke device miliknya
    - operator: Pekerja kandang, lihat + kontrol device yang di-assign
    - viewer: Pengamat, hanya bisa lihat data device yang di-assign (read-only)
    - user: Default saat register, belum bisa akses device apapun
    """
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    USER = "user"

    @classmethod
    def admin_roles(cls):
        """Role yang bisa akses admin dashboard"""
        return [cls.SUPER_ADMIN.value, cls.ADMIN.value]

    @classmethod
    def can_control_roles(cls):
        """Role yang bisa kontrol device (jika punya akses)"""
        return [cls.SUPER_ADMIN.value, cls.ADMIN.value, cls.OPERATOR.value]

    @classmethod
    def can_view_roles(cls):
        """Role yang bisa lihat data device (jika punya akses)"""
        return [cls.SUPER_ADMIN.value, cls.ADMIN.value, cls.OPERATOR.value, cls.VIEWER.value]


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    provider = Column(String, default="firebase")
    is_active = Column(Boolean, default=True)
    role = Column(String, nullable=False, default=UserRole.USER.value)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    devices = relationship("Device", back_populates="owner")
