import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models.user import User, UserRole
from app.core.security import verify_token

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Dependency dasar: ambil user yang sedang login dari JWT token.
    Semua endpoint yang butuh autentikasi menggunakan dependency ini.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak diberikan",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    payload = verify_token(token)
    if payload is None:
        logger.warning("Auth GAGAL - Token tidak valid atau expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kadaluarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        logger.warning("Auth GAGAL - Token tanpa user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token rusak (tidak ada ID user)",
        )

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.warning(f"Auth GAGAL - Format UUID tidak valid: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token rusak (format ID user tidak valid)",
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        logger.warning(f"Auth GAGAL - User tidak ditemukan di DB: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User tidak ditemukan",
        )

    logger.debug(f"Auth SUKSES - User {user.email} (role: {user.role})")
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
):
    """
    Dependency untuk endpoint admin dashboard.
    Mengizinkan: super_admin DAN admin.
    """
    if current_user.role not in UserRole.admin_roles():
        logger.warning(f"Akses Admin DITOLAK untuk {current_user.email} (role: {current_user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Endpoint ini khusus Admin.",
        )
    return current_user


async def get_current_super_admin(
    current_user: User = Depends(get_current_user)
):
    """
    Dependency untuk endpoint yang hanya bisa diakses super_admin.
    Contoh: sync Firebase users, register device.
    """
    if current_user.role != UserRole.SUPER_ADMIN.value:
        logger.warning(f"Akses Super Admin DITOLAK untuk {current_user.email} (role: {current_user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Endpoint ini khusus Super Admin.",
        )
    return current_user


def get_device_with_access(device_id: UUID, current_user: User, db: Session):
    """
    Cek apakah user punya akses ke device tertentu.
    
    Aturan akses:
    - super_admin: akses SEMUA device
    - admin: akses device miliknya (user_id == admin.id)
    - operator/viewer: akses device yang di-assign via device_assignments
    - user: TIDAK bisa akses device apapun
    
    Returns: Device object jika punya akses, raise 404 jika tidak.
    """
    from app.models.device import Device, DeviceAssignment

    # Super Admin bisa akses semua device
    if current_user.role == UserRole.SUPER_ADMIN.value:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device tidak ditemukan")
        return device

    # Admin bisa akses device miliknya
    if current_user.role == UserRole.ADMIN.value:
        device = db.query(Device).filter(
            Device.id == device_id,
            Device.user_id == current_user.id
        ).first()
        if device:
            return device
        raise HTTPException(status_code=404, detail="Device tidak ditemukan atau akses ditolak")

    # Operator dan Viewer bisa akses device yang di-assign
    if current_user.role in [UserRole.OPERATOR.value, UserRole.VIEWER.value]:
        assignment = db.query(DeviceAssignment).filter(
            DeviceAssignment.device_id == device_id,
            DeviceAssignment.user_id == current_user.id
        ).first()
        if assignment:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device:
                return device
        raise HTTPException(status_code=404, detail="Device tidak ditemukan atau akses ditolak")

    # User default: tidak bisa akses device apapun
    raise HTTPException(status_code=403, detail="Akses ditolak. Hubungi admin untuk mendapatkan akses ke device.")


def check_can_control_device(device_id: UUID, current_user: User, db: Session):
    """
    Cek apakah user bisa KONTROL device (bukan hanya lihat).
    
    Yang bisa kontrol:
    - super_admin: semua device
    - admin: device miliknya
    - operator: device yang di-assign
    
    Yang TIDAK bisa kontrol:
    - viewer: hanya bisa lihat (read-only)
    - user: tidak bisa akses sama sekali
    """
    # Viewer tidak bisa kontrol
    if current_user.role == UserRole.VIEWER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Viewer hanya bisa melihat data, tidak bisa mengontrol device."
        )

    # User default tidak bisa kontrol
    if current_user.role == UserRole.USER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Hubungi admin untuk mendapatkan akses ke device."
        )

    # Cek akses ke device (super_admin, admin, operator)
    return get_device_with_access(device_id, current_user, db)
