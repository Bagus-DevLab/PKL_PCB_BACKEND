import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
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

    # Query 1: User counts per role (1 query instead of 5)
    role_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    role_map = dict(role_counts)
    total_users = sum(role_map.values())
    total_super_admins = role_map.get(UserRole.SUPER_ADMIN.value, 0)
    total_admins = role_map.get(UserRole.ADMIN.value, 0)
    total_operators = role_map.get(UserRole.OPERATOR.value, 0)
    total_viewers = role_map.get(UserRole.VIEWER.value, 0)

    # Query 2: Device counts with conditional aggregation (1 query instead of 4)
    online_cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.DEVICE_ONLINE_TIMEOUT_SECONDS)
    device_stats = db.query(
        func.count(Device.id),
        func.count(case((Device.user_id.isnot(None), 1))),
        func.count(case((Device.user_id.is_(None), 1))),
        func.count(case((Device.last_heartbeat >= online_cutoff, 1))),
    ).first()
    total_devices = device_stats[0]
    total_devices_claimed = device_stats[1]
    total_devices_unclaimed = device_stats[2]
    total_devices_online = device_stats[3]

    # Query 3: Assignment count (1 query, unchanged)
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
    return paginate(query, page, limit, schema=UserResponse)


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


@router.post("/cleanup-logs")
@limiter.limit("5/minute")
def cleanup_old_sensor_logs(
    request: Request,
    days: int = Query(
        default=None,
        ge=1,
        description="Hapus logs lebih lama dari N hari. Default: SENSOR_LOG_RETENTION_DAYS dari .env"
    ),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_super_admin)
):
    """
    Hapus sensor logs yang lebih lama dari retention period.
    Khusus Super Admin. Rate limited: 5x per menit.
    
    - Jika `days` tidak diberikan, gunakan SENSOR_LOG_RETENTION_DAYS dari .env (default 365).
    - Jika SENSOR_LOG_RETENTION_DAYS = 0, cleanup di-disable (return error).
    """
    from datetime import datetime, timezone, timedelta
    from app.models.device import SensorLog

    retention_days = days if days is not None else settings.SENSOR_LOG_RETENTION_DAYS

    if retention_days == 0:
        raise HTTPException(
            status_code=400,
            detail="Data retention di-disable (SENSOR_LOG_RETENTION_DAYS=0). Tidak ada data yang dihapus."
        )

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    # Hitung dulu berapa yang akan dihapus (estimasi)
    count_to_delete = db.query(func.count(SensorLog.id)).filter(
        SensorLog.timestamp < cutoff_date
    ).scalar()

    if count_to_delete == 0:
        return {
            "status": "success",
            "message": f"Tidak ada sensor logs yang lebih lama dari {retention_days} hari.",
            "deleted_count": 0,
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
        }

    # Hapus data lama dalam batch untuk menghindari long-running lock
    BATCH_SIZE = 1000
    total_deleted = 0

    while True:
        # Ambil batch ID yang akan dihapus
        batch_ids = db.query(SensorLog.id).filter(
            SensorLog.timestamp < cutoff_date
        ).limit(BATCH_SIZE).all()

        if not batch_ids:
            break

        ids = [row[0] for row in batch_ids]
        deleted = db.query(SensorLog).filter(
            SensorLog.id.in_(ids)
        ).delete(synchronize_session=False)

        db.commit()
        total_deleted += deleted

    logger.warning(
        f"CLEANUP oleh {admin_user.email}: {total_deleted} sensor logs dihapus "
        f"(lebih lama dari {retention_days} hari, cutoff: {cutoff_date.isoformat()})"
    )

    return {
        "status": "success",
        "message": f"{total_deleted} sensor logs berhasil dihapus.",
        "deleted_count": total_deleted,
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat(),
    }
