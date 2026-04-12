import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session # Tambahan: Butuh ini buat typing db
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db # Tambahan: Butuh fungsi session database lo
from app.models.user import User
from app.schemas.user import UserResponse # Tambahan: Butuh schema buat response_model
from app.dependencies import get_current_user
from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/users", 
    tags=["Users"]
)
# 0. Endpoint Ambil Data Profil (Yang Kelupaan)
@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """Mengambil data profil user yang sedang login"""
    return current_user

# 1. Endpoint Update Nama
# Pakai query parameter ?full_name=...
@router.patch("/me", response_model=UserResponse)
def update_user_me(
    full_name: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.id} mengupdate nama menjadi: {full_name}")
    current_user.full_name = full_name
    db.commit()
    db.refresh(current_user)
    return current_user

# 2. Endpoint Hapus Akun
@router.delete("/me")
def delete_user_me(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    logger.warning(f"User {current_user.id} menghapus akun selamanya.")
    db.delete(current_user)
    db.commit()
    return {"message": "Akun berhasil dihapus dari database lokal"}