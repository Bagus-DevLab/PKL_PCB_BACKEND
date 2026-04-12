import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    
    # Boleh kosong (nullable=True) karena user Google tidak punya password
    hashed_password = Column(String, nullable=True) 
    
    # Boleh kosong karena user lokal (register manual) mungkin tidak upload foto
    picture = Column(String, nullable=True)
    
    # Penanda metode login ("local" untuk email/pass, "google" untuk OAuth)
    provider = Column(String, default="local") 
    
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    devices = relationship("Device", back_populates="owner")