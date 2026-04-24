import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User, UserRole
from app.models.device import Device
from app.schemas.user import UserResponse, UpdateUserRole, UpdateUserName
from app.dependencies import get_current_user, get_current_admin

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
@router.patch("/me", response_model=UserResponse)
def update_user_me(
    data: UpdateUserName,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Update nama user yang sedang login. Nama harus 1-100 karakter."""
    logger.info(f"User {current_user.id} mengupdate nama menjadi: {data.full_name}")
    current_user.full_name = data.full_name
    db.commit()
    db.refresh(current_user)
    return current_user

# 2. Endpoint Hapus Akun
@router.delete("/me")
def delete_user_me(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    logger.warning(f"User {current_user.id} ({current_user.email}) menghapus akun selamanya.")
    
    # Unclaim semua device milik user sebelum hapus akun
    # agar device bisa diklaim ulang oleh user lain
    unclaimed_count = db.query(Device).filter(
        Device.user_id == current_user.id
    ).update({"user_id": None, "name": None})
    
    if unclaimed_count > 0:
        logger.info(f"{unclaimed_count} device di-unclaim karena user {current_user.email} hapus akun")
    
    db.delete(current_user)
    db.commit()
    return {"message": "Akun berhasil dihapus dari database lokal"}


# ==========================================
# 3. MANAGE ROLE (KHUSUS ADMIN)
# ==========================================

@router.patch("/{user_id}/role", response_model=UserResponse)
@limiter.limit("10/minute")
def update_user_role(
    request: Request,
    user_id: UUID,
    role_update: UpdateUserRole,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Mengubah role user lain. Khusus Admin.
    
    - Admin tidak bisa mengubah role dirinya sendiri (mencegah lock-out).
    - Role yang valid: "admin" atau "user".
    """
    # Cegah admin mengubah role dirinya sendiri
    if user_id == admin_user.id:
        logger.warning(f"Admin {admin_user.email} mencoba mengubah role dirinya sendiri")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak bisa mengubah role diri sendiri!"
        )
    
    # Cari target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        logger.warning(f"Update role GAGAL - User {user_id} tidak ditemukan oleh {admin_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User tidak ditemukan"
        )
    
    old_role = target_user.role
    target_user.role = role_update.role
    db.commit()
    db.refresh(target_user)
    
    logger.info(
        f"Role DIUBAH - User {target_user.email}: {old_role} -> {role_update.role} "
        f"oleh admin {admin_user.email}"
    )
    return target_user