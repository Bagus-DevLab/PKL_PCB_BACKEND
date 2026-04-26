import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, Integer, String
from typing import List
from uuid import UUID
from app.core.limiter import limiter
from app.database import get_db
from app.models.user import User, UserRole
from app.models.device import Device, SensorLog, DeviceAssignment
from app.schemas import DeviceClaim, DeviceResponse, LogResponse, DeviceRegister, DeviceUpdate
from app.schemas.device import (
    DeviceControl, DailyTemperatureStats, DailyTemperatureStatsResponse,
    DeviceAssignmentCreate, DeviceAssignmentResponse,
)
from app.dependencies import (
    get_current_user, get_current_admin, get_current_super_admin,
    get_device_with_access, check_can_control_device, get_owned_device,
)
from app.mqtt.publisher import publish_control
from app.core.config import settings
from app.core.pagination import paginate
from datetime import date as date_type, datetime, timezone, timedelta
import asyncio
from app.core.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)


def _close_device_websockets(device_id: str, reason: str = "Device dihapus"):
    """
    Schedule WebSocket cleanup dari sync context.
    Sync endpoints berjalan di threadpool, jadi kita gunakan
    run_coroutine_threadsafe untuk menjadwalkan async close di event loop.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                ws_manager.close_device_connections(device_id, reason=reason),
                loop,
            )
        else:
            logger.debug("Event loop not running, skipping WS cleanup")
    except RuntimeError:
        logger.debug("No event loop available, skipping WS cleanup")


def _check_and_downgrade_role(db: Session, user_id: UUID) -> None:
    """
    Cek apakah user perlu di-downgrade role-nya setelah assignment dihapus.
    
    Logika:
    - Jika user adalah admin/super_admin, SKIP (role mereka bukan dari assignment).
    - Jika sisa assignment = 0, downgrade ke "user".
    - Jika sisa assignment > 0, hitung role tertinggi dari assignment yang tersisa:
      - Ada "operator" → role = "operator"
      - Hanya "viewer"  → role = "viewer"
    
    PENTING: Fungsi ini TIDAK memanggil db.commit().
    Caller bertanggung jawab atas commit agar tetap transactionally safe.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    # Jangan sentuh role admin-tier — mereka tidak bergantung pada assignment
    if user.role in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        return

    remaining = db.query(DeviceAssignment.role).filter(
        DeviceAssignment.user_id == user_id
    ).all()

    if len(remaining) == 0:
        if user.role in [UserRole.OPERATOR.value, UserRole.VIEWER.value]:
            old_role = user.role
            db.query(User).filter(User.id == user_id).update(
                {"role": UserRole.USER.value},
                synchronize_session=False
            )
            logger.info(f"Role DOWNGRADE - {user.email}: {old_role} -> user (0 assignment tersisa)")
    else:
        roles = {r[0] for r in remaining}
        highest = UserRole.OPERATOR.value if UserRole.OPERATOR.value in roles else UserRole.VIEWER.value
        if user.role != highest:
            old_role = user.role
            db.query(User).filter(User.id == user_id).update(
                {"role": highest},
                synchronize_session=False
            )
            logger.info(f"Role ADJUSTED - {user.email}: {old_role} -> {highest} (sesuai assignment tersisa)")


# ==========================================
# 0. REGISTER DEVICE (KHUSUS SUPER ADMIN)
# ==========================================
@router.post("/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def register_device(
    request: Request,
    device_in: DeviceRegister,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_super_admin)
):
    """Mendaftarkan MAC Address device baru. Khusus Super Admin."""
    logger.info(f"Super Admin {admin_user.email} mendaftarkan device baru MAC: {device_in.mac_address}")

    existing_device = db.query(Device).filter(Device.mac_address == device_in.mac_address).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Perangkat dengan MAC Address tersebut sudah terdaftar!")

    new_device = Device(mac_address=device_in.mac_address, name=None, user_id=None)
    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    logger.info(f"Register SUKSES - Device {new_device.mac_address} oleh {admin_user.email}")
    return new_device


# ==========================================
# 1. KLAIM DEVICE (SUPER ADMIN + ADMIN)
# ==========================================
@router.post("/claim", response_model=DeviceResponse)
@limiter.limit("10/minute")
def claim_device(
    request: Request,
    device_in: DeviceClaim,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Klaim device via QR Code. Hanya Super Admin dan Admin."""
    # Cek role: hanya super_admin dan admin yang bisa claim
    if current_user.role not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Hanya Admin yang bisa mengklaim device.")

    logger.info(f"{current_user.role} {current_user.email} mencoba klaim device MAC: {device_in.mac_address}")

    device = db.query(Device).filter(Device.mac_address == device_in.mac_address).with_for_update().first()
    if not device:
        raise HTTPException(status_code=404, detail="Device tidak dikenali! Pastikan Anda memindai QR Code produk asli.")

    if device.user_id is not None:
        raise HTTPException(status_code=400, detail="Device ini sudah diklaim oleh pengguna lain!")

    device.user_id = current_user.id
    device.name = device_in.name
    db.commit()
    db.refresh(device)

    logger.info(f"Klaim SUKSES - Device {device.mac_address} diklaim oleh {current_user.email}")
    return device


# ==========================================
# 2. LIHAT DEVICE (BERDASARKAN ROLE)
# ==========================================
@router.get("/")
@limiter.limit("30/minute")
def read_my_devices(
    request: Request,
    page: int = Query(default=1, ge=1, description="Nomor halaman"),
    limit: int = Query(default=20, ge=1, le=100, description="Item per halaman"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List device berdasarkan role (dengan pagination):
    - super_admin: semua device
    - admin: device miliknya
    - operator/viewer: device yang di-assign
    - user: empty list
    """
    if current_user.role == UserRole.SUPER_ADMIN.value:
        query = db.query(Device)
    elif current_user.role == UserRole.ADMIN.value:
        query = db.query(Device).filter(Device.user_id == current_user.id)
    elif current_user.role in [UserRole.OPERATOR.value, UserRole.VIEWER.value]:
        assigned_device_ids = db.query(DeviceAssignment.device_id).filter(
            DeviceAssignment.user_id == current_user.id
        ).scalar_subquery()
        query = db.query(Device).filter(Device.id.in_(assigned_device_ids))
    else:
        return {"data": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}

    return paginate(query, page, limit, schema=DeviceResponse)


# ==========================================
# 2.5 LIHAT DEVICE BELUM DIKLAIM (ADMIN+)
# ==========================================
@router.get("/unclaimed")
@limiter.limit("30/minute")
def get_unclaimed_devices(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Daftar device yang belum diklaim. Khusus Admin+."""
    query = db.query(Device).filter(Device.user_id == None)
    return paginate(query, page, limit, schema=DeviceResponse)


# ==========================================
# 2.6 LIHAT SEMUA DEVICE (ADMIN+)
# ==========================================
@router.get("/all")
@limiter.limit("30/minute")
def get_all_devices(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Daftar SEMUA device (claimed + unclaimed) dengan pagination. Khusus Admin+.
    - Super Admin: lihat semua device
    - Admin: lihat device miliknya + unclaimed
    """
    if admin_user.role == UserRole.SUPER_ADMIN.value:
        query = db.query(Device).order_by(Device.created_at.desc())
    else:
        query = db.query(Device).filter(
            (Device.user_id == admin_user.id) | (Device.user_id == None)
        ).order_by(Device.created_at.desc())
    return paginate(query, page, limit, schema=DeviceResponse)


# ==========================================
# 2.7 EDIT DEVICE (RENAME)
# ==========================================
@router.patch("/{device_id}", response_model=DeviceResponse)
@limiter.limit("20/minute")
def update_device(
    request: Request,
    device_id: UUID,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Edit nama device.
    - Super Admin: edit device manapun
    - Admin: edit device miliknya
    """
    device = get_owned_device(device_id, current_user, db)

    old_name = device.name
    device.name = data.name
    db.commit()
    db.refresh(device)

    logger.info(f"Device DIUBAH - '{old_name}' -> '{data.name}' oleh {current_user.email}")
    return device


# ==========================================
# 2.8 HAPUS DEVICE (SUPER ADMIN ONLY)
# ==========================================
@router.delete("/{device_id}")
@limiter.limit("10/minute")
def delete_device(
    request: Request,
    device_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_super_admin)
):
    """
    Hapus device beserta semua data terkait (sensor logs, assignments).
    Khusus Super Admin. Operasi ini IRREVERSIBLE.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device tidak ditemukan")

    mac = device.mac_address
    name = device.name

    # Kumpulkan user_id yang terdampak SEBELUM assignment dihapus
    affected_user_ids = [
        row[0] for row in db.query(DeviceAssignment.user_id).filter(
            DeviceAssignment.device_id == device_id
        ).distinct().all()
    ]

    # Hapus semua data terkait
    deleted_assignments = db.query(DeviceAssignment).filter(DeviceAssignment.device_id == device_id).delete()
    deleted_logs = db.query(SensorLog).filter(SensorLog.device_id == device_id).delete()

    # Downgrade role user yang tidak punya assignment lagi
    for uid in affected_user_ids:
        _check_and_downgrade_role(db, uid)

    db.delete(device)
    db.commit()

    # Tutup semua WebSocket connections yang sedang streaming device ini
    _close_device_websockets(str(device_id))

    logger.warning(
        f"Device DIHAPUS - {mac} ('{name}') oleh Super Admin {admin_user.email}. "
        f"Dihapus: {deleted_logs} logs, {deleted_assignments} assignments."
    )
    return {
        "status": "success",
        "message": f"Device {mac} berhasil dihapus beserta {deleted_logs} sensor logs dan {deleted_assignments} assignments."
    }


# ==========================================
# 3. LIHAT DATA SENSOR (DENGAN ACCESS CHECK)
# ==========================================
@router.get("/{device_id}/logs")
@limiter.limit("60/minute")
def read_device_logs(
    request: Request,
    device_id: UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lihat history data sensor dengan pagination. Semua role yang punya akses ke device."""
    device = get_device_with_access(device_id, current_user, db)

    query = db.query(SensorLog)\
        .filter(SensorLog.device_id == device_id)\
        .order_by(SensorLog.timestamp.desc())

    return paginate(query, page, limit, schema=LogResponse)


# ==========================================
# 3.5 KONTROL DEVICE (ADMIN + OPERATOR)
# ==========================================
@router.post("/{device_id}/control")
@limiter.limit("30/minute")
def control_device(
    request: Request,
    device_id: UUID,
    command: DeviceControl,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kontrol device. Hanya Super Admin, Admin (pemilik), dan Operator (assigned)."""
    logger.info(f"User {current_user.email} mengirim kontrol ke device_id: {device_id}")

    device = check_can_control_device(device_id, current_user, db)

    try:
        publish_control(device.mac_address, command.component, command.state)
        logger.info(f"Kontrol SUKSES - {command.component} {'ON' if command.state else 'OFF'} ke {device.name}")
        return {"status": "success", "message": f"Perintah {command.component} dikirim ke {device.name}"}
    except Exception as e:
        logger.error(f"Kontrol GAGAL - MQTT Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Gagal mengirim perintah ke device.")


# ==========================================
# 4. LIHAT ALERTS (DENGAN ACCESS CHECK)
# ==========================================
@router.get("/{device_id}/alerts")
@limiter.limit("60/minute")
def get_device_alerts(
    request: Request,
    device_id: UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lihat riwayat alert dengan pagination. Semua role yang punya akses ke device."""
    device = get_device_with_access(device_id, current_user, db)

    query = db.query(SensorLog)\
        .filter(SensorLog.device_id == device_id, SensorLog.is_alert == True)\
        .order_by(SensorLog.timestamp.desc())

    return paginate(query, page, limit, schema=LogResponse)


# ==========================================
# 5. STATISTIK HARIAN (DENGAN ACCESS CHECK)
# ==========================================
@router.get("/{device_id}/stats/daily", response_model=DailyTemperatureStatsResponse)
@limiter.limit("30/minute")
def get_daily_temperature_stats(
    request: Request,
    device_id: UUID,
    days: int = Query(default=7, ge=1, le=90, description="Jumlah hari ke belakang (1-90)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Statistik rata-rata suhu harian. Semua role yang punya akses ke device."""
    logger.info(f"User {current_user.email} mengambil statistik harian device_id: {device_id}, days: {days}")

    device = get_device_with_access(device_id, current_user, db)

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)
    start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)

    log_date = func.date(SensorLog.timestamp, type_=String).label("log_date")

    daily_stats = db.query(
        log_date,
        func.avg(SensorLog.temperature).label("avg_temperature"),
        func.min(SensorLog.temperature).label("min_temperature"),
        func.max(SensorLog.temperature).label("max_temperature"),
        func.avg(SensorLog.humidity).label("avg_humidity"),
        func.avg(SensorLog.ammonia).label("avg_ammonia"),
        func.count(SensorLog.id).label("data_points"),
        func.sum(cast(SensorLog.is_alert, Integer)).label("alert_count"),
    ).filter(
        SensorLog.device_id == device_id,
        SensorLog.timestamp >= start_datetime
    ).group_by(log_date).order_by(log_date.asc()).all()

    statistics = []
    for row in daily_stats:
        log_date_value = row.log_date
        if isinstance(log_date_value, str):
            log_date_value = date_type.fromisoformat(log_date_value)

        stat = DailyTemperatureStats(
            date=log_date_value,
            avg_temperature=row.avg_temperature or 0.0,
            min_temperature=row.min_temperature or 0.0,
            max_temperature=row.max_temperature or 0.0,
            avg_humidity=row.avg_humidity or 0.0,
            avg_ammonia=row.avg_ammonia or 0.0,
            data_points=row.data_points or 0,
            alert_count=row.alert_count or 0,
        )
        statistics.append(stat)

    response = DailyTemperatureStatsResponse(
        device_id=device.id,
        device_name=device.name,
        period_start=start_date,
        period_end=today,
        total_days=len(statistics),
        statistics=statistics
    )

    logger.info(f"Stats SUKSES - Device '{device.name}': {len(statistics)} hari data")
    return response


# ==========================================
# 6. UNCLAIM DEVICE (SUPER ADMIN + ADMIN PEMILIK)
# ==========================================
@router.post("/{device_id}/unclaim")
@limiter.limit("10/minute")
def unclaim_device(
    request: Request,
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lepas kepemilikan device. Hanya Super Admin atau Admin pemilik."""
    device = get_owned_device(device_id, current_user, db)

    old_name = device.name

    # Kumpulkan user_id yang terdampak SEBELUM assignment dihapus
    affected_user_ids = [
        row[0] for row in db.query(DeviceAssignment.user_id).filter(
            DeviceAssignment.device_id == device_id
        ).distinct().all()
    ]

    # Hapus semua assignment terkait device ini
    db.query(DeviceAssignment).filter(DeviceAssignment.device_id == device_id).delete()

    # Downgrade role user yang tidak punya assignment lagi
    for uid in affected_user_ids:
        _check_and_downgrade_role(db, uid)

    device.user_id = None
    device.name = None
    db.commit()

    # Tutup semua WebSocket connections — akses sudah berubah
    _close_device_websockets(str(device_id), reason="Device di-unclaim")

    logger.info(f"Unclaim SUKSES - Device '{old_name}' dilepas oleh {current_user.email}")
    return {"status": "success", "message": "Device berhasil di-unclaim."}


# ==========================================
# 7. STATUS DEVICE (DENGAN ACCESS CHECK)
# ==========================================
@router.get("/{device_id}/status")
@limiter.limit("60/minute")
def get_device_status(
    request: Request,
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cek status online/offline device."""
    device = get_device_with_access(device_id, current_user, db)

    if not device.last_heartbeat:
        return {"device_id": device_id, "is_online": False, "last_seen": None, "message": "Belum ada koneksi"}

    now = datetime.now(timezone.utc)
    last_hb = device.last_heartbeat
    if last_hb.tzinfo is None:
        last_hb = last_hb.replace(tzinfo=timezone.utc)

    seconds_since = (now - last_hb).total_seconds()
    is_online = seconds_since <= settings.DEVICE_ONLINE_TIMEOUT_SECONDS

    return {
        "device_id": device_id,
        "is_online": is_online,
        "last_seen": last_hb,
        "seconds_since_last_seen": round(seconds_since)
    }


# ==========================================
# 8. DEVICE ASSIGNMENT (ADMIN ASSIGN USER KE DEVICE)
# ==========================================
@router.post("/{device_id}/assign", response_model=DeviceAssignmentResponse)
@limiter.limit("20/minute")
def assign_user_to_device(
    request: Request,
    device_id: UUID,
    assignment: DeviceAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign user (operator/viewer) ke device.
    - Super Admin: bisa assign ke device manapun
    - Admin: hanya bisa assign ke device miliknya
    """
    device = get_owned_device(device_id, current_user, db)

    # Cek target user
    target_user = db.query(User).filter(User.id == assignment.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")

    # Tidak bisa assign diri sendiri
    if assignment.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Tidak bisa assign diri sendiri.")

    # Tidak bisa assign super_admin atau admin
    if target_user.role in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=400, detail="Tidak perlu assign Admin/Super Admin — mereka sudah punya akses.")

    # Cek apakah sudah di-assign
    existing = db.query(DeviceAssignment).filter(
        DeviceAssignment.device_id == device_id,
        DeviceAssignment.user_id == assignment.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User sudah di-assign ke device ini.")

    # Buat assignment
    new_assignment = DeviceAssignment(
        device_id=device_id,
        user_id=assignment.user_id,
        assigned_by=current_user.id,
        role=assignment.role,
    )
    db.add(new_assignment)

    # Update role user jika masih "user" (default)
    if target_user.role == UserRole.USER.value:
        target_user.role = assignment.role
        logger.info(f"User {target_user.email} otomatis di-upgrade ke {assignment.role}")

    db.commit()
    db.refresh(new_assignment)

    logger.info(f"Assignment SUKSES - {target_user.email} ({assignment.role}) -> device {device.name} oleh {current_user.email}")

    return DeviceAssignmentResponse(
        id=new_assignment.id,
        device_id=new_assignment.device_id,
        user_id=new_assignment.user_id,
        user_email=target_user.email,
        user_name=target_user.full_name,
        role=new_assignment.role,
        assigned_by=new_assignment.assigned_by,
        created_at=new_assignment.created_at,
    )


@router.delete("/{device_id}/assign/{user_id}")
@limiter.limit("20/minute")
def unassign_user_from_device(
    request: Request,
    device_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hapus assignment user dari device."""
    device = get_owned_device(device_id, current_user, db)

    assignment = db.query(DeviceAssignment).filter(
        DeviceAssignment.device_id == device_id,
        DeviceAssignment.user_id == user_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment tidak ditemukan.")

    target_user = db.query(User).filter(User.id == user_id).first()
    db.delete(assignment)
    db.flush()  # Flush pending delete agar query count di helper melihat state yang benar

    # Cek apakah user perlu di-downgrade setelah assignment dihapus
    _check_and_downgrade_role(db, user_id)

    db.commit()

    logger.info(f"Unassign SUKSES - {target_user.email if target_user else user_id} dari device {device.name}")
    return {"status": "success", "message": "User berhasil di-unassign dari device."}


@router.get("/{device_id}/assignments", response_model=List[DeviceAssignmentResponse])
@limiter.limit("30/minute")
def get_device_assignments(
    request: Request,
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lihat siapa saja yang di-assign ke device. Khusus Admin+."""
    device = get_owned_device(device_id, current_user, db)

    assignments = db.query(DeviceAssignment).options(
        joinedload(DeviceAssignment.user)
    ).filter(DeviceAssignment.device_id == device_id).all()

    result = []
    for a in assignments:
        result.append(DeviceAssignmentResponse(
            id=a.id,
            device_id=a.device_id,
            user_id=a.user_id,
            user_email=a.user.email if a.user else None,
            user_name=a.user.full_name if a.user else None,
            role=a.role,
            assigned_by=a.assigned_by,
            created_at=a.created_at,
        ))

    return result
