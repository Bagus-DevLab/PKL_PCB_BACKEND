from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.security import verify_token

# Ini biar di Swagger UI nanti muncul tombol "Authorize" (Gembok)
# Url 'auth/google/login' cuma dummy biar swagger gak error
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/google/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """
    Dependency ini tugasnya:
    1. Ambil token dari Header 'Authorization: Bearer ...'
    2. Validasi token (asli/palsu/expired?)
    3. Cari user di DB berdasarkan ID di dalam token
    4. Kalau semua oke, return object User.
    """
    
    # 1. Cek Token Valid Gak?
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kadaluarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Ambil ID User dari dalam token (sub)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token rusak (tidak ada ID user)",
        )
        
    # 3. Cek apakah user beneran ada di DB?
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan",
        )
        
    return user