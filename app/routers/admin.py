import logging
from fastapi import APIRouter, Depends, HTTPException, Request
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
from app.core.config import settings

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


@router.post("/sync-firebase-users")
@limiter.limit("5/minute")
def sync_firebase_users(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Sinkronisasi user dari Firebase Auth ke PostgreSQL.
    
    Mengambil semua user yang terdaftar di Firebase Auth,
    lalu membuat record di PostgreSQL untuk user yang belum ada.
    User yang sudah ada di PostgreSQL TIDAK akan diubah.
    
    Khusus Admin. Rate limited: 5x per menit.
    """
    try:
        from firebase_admin import auth as firebase_auth
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Firebase Admin SDK tidak tersedia di server."
        )

    logger.info(f"Admin {admin_user.email} memulai sync Firebase users")

    synced = []     # User baru yang berhasil di-sync
    skipped = []    # User yang sudah ada di PostgreSQL
    failed = []     # User yang gagal di-sync

    try:
        # Iterasi semua user di Firebase Auth (paginated)
        page = firebase_auth.list_users()
        
        while page:
            for firebase_user in page.users:
                email = firebase_user.email
                
                # Skip user tanpa email (misalnya anonymous auth)
                if not email:
                    continue
                
                # Cek apakah sudah ada di PostgreSQL
                existing = db.query(User).filter(User.email == email).first()
                
                if existing:
                    skipped.append(email)
                    continue
                
                # Buat user baru di PostgreSQL
                try:
                    # Tentukan role
                    role = UserRole.USER.value
                    if settings.INITIAL_ADMIN_EMAIL and email == settings.INITIAL_ADMIN_EMAIL:
                        role = UserRole.ADMIN.value
                    
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
                    
                    logger.info(f"Sync: User baru {email} (role: {role}) ditambahkan ke PostgreSQL")
                    
                except Exception as e:
                    db.rollback()
                    failed.append({"email": email, "error": str(e)})
                    logger.error(f"Sync GAGAL untuk {email}: {str(e)}")
            
            # Halaman berikutnya (Firebase pagination)
            page = page.get_next_page()

    except Exception as e:
        logger.error(f"Sync Firebase users GAGAL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Gagal mengambil data dari Firebase: {str(e)}"
        )

    result = {
        "synced_count": len(synced),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "synced": synced,
        "skipped": skipped,
        "failed": failed,
    }

    logger.info(
        f"Sync selesai oleh {admin_user.email}: "
        f"{len(synced)} baru, {len(skipped)} sudah ada, {len(failed)} gagal"
    )

    return result
