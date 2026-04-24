import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.limiter import limiter
from app.database import get_db
from app.models.user import User, UserRole
from app.models.device import Device, DeviceAssignment
from app.schemas.user import UserResponse, UpdateUserRole, UpdateUserName
from app.dependencies import get_current_user, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """Mengambil data profil user yang sedang login"""
    return current_user


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


@router.delete("/me")
def delete_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hapus akun user yang sedang login."""
    logger.warning(f"User {current_user.id} ({current_user.email}) menghapus akun selamanya.")

    # Hapus semua assignment terkait user ini
    db.query(DeviceAssignment).filter(DeviceAssignment.user_id == current_user.id).delete()

    # Unclaim semua device milik user
    unclaimed_count = db.query(Device).filter(
        Device.user_id == current_user.id
    ).update({"user_id": None, "name": None})

    if unclaimed_count > 0:
        logger.info(f"{unclaimed_count} device di-unclaim karena user {current_user.email} hapus akun")

    db.delete(current_user)
    db.commit()
    return {"message": "Akun berhasil dihapus dari database lokal"}


# ==========================================
# MANAGE ROLE (DENGAN HIERARCHY)
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
    Mengubah role user lain.
    
    Aturan hierarchy:
    - Super Admin: bisa set semua role (super_admin, admin, operator, viewer, user)
    - Admin: hanya bisa set operator, viewer, atau user
    - Admin tidak bisa promote ke admin atau super_admin
    - Tidak bisa mengubah role diri sendiri
    """
    # Cegah ubah role diri sendiri
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak bisa mengubah role diri sendiri!"
        )

    # Cari target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    # Enforce hierarchy
    if admin_user.role == UserRole.ADMIN.value:
        # Admin hanya bisa set: operator, viewer, user
        allowed_roles = [UserRole.OPERATOR.value, UserRole.VIEWER.value, UserRole.USER.value]
        if role_update.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Admin hanya bisa mengatur role: {', '.join(allowed_roles)}"
            )
        # Admin tidak bisa mengubah role super_admin atau admin lain
        if target_user.role in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak bisa mengubah role Super Admin atau Admin lain."
            )

    # Super Admin bisa set semua role, tapi tidak bisa demote super_admin lain
    if admin_user.role == UserRole.SUPER_ADMIN.value:
        if target_user.role == UserRole.SUPER_ADMIN.value and role_update.role != UserRole.SUPER_ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak bisa mengubah role Super Admin lain. Hubungi developer."
            )

    old_role = target_user.role
    target_user.role = role_update.role
    db.commit()
    db.refresh(target_user)

    logger.info(
        f"Role DIUBAH - User {target_user.email}: {old_role} -> {role_update.role} "
        f"oleh {admin_user.role} {admin_user.email}"
    )
    return target_user
