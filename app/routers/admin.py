import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User, UserRole
from app.models.device import Device
from app.schemas.user import UserResponse
from app.dependencies import get_current_admin

logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/stats")
@limiter.limit("30/minute")
def get_admin_stats(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Dashboard overview untuk admin.
    Menampilkan ringkasan jumlah user, device, dan status sistem.
    """
    from datetime import datetime, timezone, timedelta

    logger.info(f"Admin {admin_user.email} mengakses dashboard stats")

    # Hitung jumlah user per role
    total_users = db.query(func.count(User.id)).scalar()
    total_admins = db.query(func.count(User.id)).filter(
        User.role == UserRole.ADMIN.value
    ).scalar()

    # Hitung jumlah device
    total_devices = db.query(func.count(Device.id)).scalar()
    total_devices_claimed = db.query(func.count(Device.id)).filter(
        Device.user_id.isnot(None)
    ).scalar()
    total_devices_unclaimed = db.query(func.count(Device.id)).filter(
        Device.user_id.is_(None)
    ).scalar()

    # Hitung device online (heartbeat dalam 5 menit terakhir)
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    total_devices_online = db.query(func.count(Device.id)).filter(
        Device.last_heartbeat.isnot(None),
        Device.last_heartbeat >= five_minutes_ago
    ).scalar()

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_devices": total_devices,
        "total_devices_claimed": total_devices_claimed,
        "total_devices_unclaimed": total_devices_unclaimed,
        "total_devices_online": total_devices_online,
    }


@router.get("/users", response_model=List[UserResponse])
@limiter.limit("30/minute")
def get_all_users(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Mengambil daftar semua user di sistem. Khusus Admin.
    Digunakan untuk halaman manage user roles di admin dashboard.
    """
    logger.info(f"Admin {admin_user.email} mengambil daftar semua user")

    users = db.query(User).order_by(User.created_at.desc()).all()
    return users
