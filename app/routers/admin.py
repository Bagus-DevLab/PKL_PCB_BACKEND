import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.core.limiter import limiter
from app.database import get_db
from app.models.user import User, UserRole
from app.models.device import Device, DeviceAssignment
from app.schemas.user import UserResponse
from app.dependencies import get_current_admin, get_current_super_admin
from app.core.config import settings
from app.core.pagination import paginate

logger = logging.getLogger(__name__)

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
    """Dashboard overview. Khusus Admin+."""
    from datetime import datetime, timezone, timedelta

    logger.info(f"{admin_user.role} {admin_user.email} mengakses dashboard stats")

    # Hitung jumlah user per role
    total_users = db.query(func.count(User.id)).scalar()
    total_super_admins = db.query(func.count(User.id)).filter(User.role == UserRole.SUPER_ADMIN.value).scalar()
    total_admins = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN.value).scalar()
    total_operators = db.query(func.count(User.id)).filter(User.role == UserRole.OPERATOR.value).scalar()
    total_viewers = db.query(func.count(User.id)).filter(User.role == UserRole.VIEWER.value).scalar()

    # Hitung jumlah device
    total_devices = db.query(func.count(Device.id)).scalar()
    total_devices_claimed = db.query(func.count(Device.id)).filter(Device.user_id.isnot(None)).scalar()
    total_devices_unclaimed = db.query(func.count(Device.id)).filter(Device.user_id.is_(None)).scalar()

    # Hitung device online
    online_cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.DEVICE_ONLINE_TIMEOUT_SECONDS)
    total_devices_online = db.query(func.count(Device.id)).filter(
        Device.last_heartbeat.isnot(None),
        Device.last_heartbeat >= online_cutoff
    ).scalar()

    # Hitung total assignments
    total_assignments = db.query(func.count(DeviceAssignment.id)).scalar()

    return {
        "total_users": total_users,
        "total_super_admins": total_super_admins,
        "total_admins": total_admins,
        "total_operators": total_operators,
        "total_viewers": total_viewers,
        "total_devices": total_devices,
        "total_devices_claimed": total_devices_claimed,
        "total_devices_unclaimed": total_devices_unclaimed,
        "total_devices_online": total_devices_online,
        "total_assignments": total_assignments,
    }


@router.get("/users")
@limiter.limit("30/minute")
def get_all_users(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Daftar semua user dengan pagination. Khusus Admin+."""
    logger.info(f"{admin_user.role} {admin_user.email} mengambil daftar user (page={page})")
    query = db.query(User).order_by(User.created_at.desc())
    return paginate(query, page, limit)


@router.post("/sync-firebase-users")
@limiter.limit("5/minute")
def sync_firebase_users(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_super_admin)
):
    """
    Sync user dari Firebase Auth ke PostgreSQL.
    Khusus Super Admin.
    """
    try:
        from firebase_admin import auth as firebase_auth
    except ImportError:
        raise HTTPException(status_code=500, detail="Firebase Admin SDK tidak tersedia.")

    logger.info(f"Super Admin {admin_user.email} memulai sync Firebase users")

    synced = []
    skipped = []
    failed = []

    try:
        page = firebase_auth.list_users()

        while page:
            for firebase_user in page.users:
                email = firebase_user.email
                if not email:
                    continue

                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    skipped.append(email)
                    continue

                try:
                    role = UserRole.USER.value
                    if settings.INITIAL_ADMIN_EMAIL and email == settings.INITIAL_ADMIN_EMAIL:
                        role = UserRole.SUPER_ADMIN.value

                    new_user = User(
                        email=email,
                        full_name=firebase_user.display_name or email.split('@')[0],
                        picture=firebase_user.photo_url or "",
                        provider="firebase",
                        role=role,
                    )
                    db.add(new_user)
                    db.commit()
                    db.refresh(new_user)
                    synced.append(email)
                    logger.info(f"Sync: User baru {email} (role: {role})")

                except Exception as e:
                    db.rollback()
                    failed.append({"email": email, "error": str(e)})
                    logger.error(f"Sync GAGAL untuk {email}: {str(e)}")

            page = page.get_next_page()

    except Exception as e:
        logger.error(f"Sync Firebase users GAGAL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gagal mengambil data dari Firebase: {str(e)}")

    result = {
        "synced_count": len(synced),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "synced": synced,
        "skipped": skipped,
        "failed": failed,
    }

    logger.info(f"Sync selesai: {len(synced)} baru, {len(skipped)} sudah ada, {len(failed)} gagal")
    return result
