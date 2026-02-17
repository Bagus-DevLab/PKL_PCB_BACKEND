import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.core.security import verify_token

logger = logging.getLogger(__name__)

# 1. Ganti Scheme jadi HTTPBearer
# Ini bikin Swagger UI cuma nampilin kotak isian token doang (Simple)
security = HTTPBearer(auto_error=False)

async def get_current_user(
    # 2. Ambil credentials dari HTTPBearer
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
):
    """
    Dependency ini tugasnya:
    1. Ambil token dari Header 'Authorization: Bearer ...'
    2. Validasi token
    3. Return user
    """
    
    # Cek apakah credentials ada (tidak ada = 401)
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak diberikan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Ambil string tokennya (karena dibungkus object credentials)
    token = credentials.credentials 

    # --- SISA LOGIC DI BAWAH INI SAMA PERSIS KAYAK SEBELUMNYA ---
    
    # Cek Token Valid Gak?
    payload = verify_token(token)
    if payload is None:
        logger.warning(f"Auth GAGAL - Token tidak valid atau expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kadaluarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Ambil ID User
    user_id: str = payload.get("sub")
    if user_id is None:
        logger.warning(f"Auth GAGAL - Token tanpa user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token rusak (tidak ada ID user)",
        )
    
    # Convert string to UUID for database query
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.warning(f"Auth GAGAL - Format UUID tidak valid: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token rusak (format ID user tidak valid)",
        )
        
    # Cek DB
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        logger.warning(f"Auth GAGAL - User tidak ditemukan di DB: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan",
        )
    
    logger.debug(f"Auth SUKSES - User {user.email} terautentikasi")
    return user