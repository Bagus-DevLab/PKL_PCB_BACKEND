import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer, String
from typing import List
from uuid import UUID
from app.core.limiter import limiter
from app.database import get_db
from app.models.user import User
from app.models.device import Device, SensorLog
from app.schemas import DeviceClaim, DeviceResponse, LogResponse, DeviceRegister
from app.dependencies import get_current_user, get_current_admin

from app.schemas.device import DeviceControl, DailyTemperatureStats, DailyTemperatureStatsResponse
from app.mqtt.publisher import publish_control
from datetime import date as date_type, datetime, timezone, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

# 0. FITUR REGISTER (KHUSUS ADMIN PABRIK)
@router.post("/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def register_device(
    request: Request,
    device_in: DeviceRegister, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin mendaftarkan MAC Address device buatan pabrik ke Database. 
    Hanya device yang sudah terdaftar di sini yang bisa diklaim oleh User.
    """
    logger.info(f"Admin {admin_user.email} mendaftarkan device baru MAC: {device_in.mac_address}")
    
    # Cek apakah device sudah ada
    existing_device = db.query(Device).filter(Device.mac_address == device_in.mac_address).first()
    if existing_device:
        logger.warning(f"Register GAGAL - MAC {device_in.mac_address} sudah terdaftar")
        raise HTTPException(
            status_code=400, 
            detail="Perangkat dengan MAC Address tersebut sudah terdaftar di sistem!"
        )

    # Buat Device baru, user_id = Null (Belum diklaim)
    new_device = Device(
        mac_address=device_in.mac_address,
        name=None,
        user_id=None
    )
    
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    logger.info(f"Register SUKSES - Device {new_device.mac_address} ditambahkan oleh {admin_user.email}")
    return new_device


# 1. FITUR KLAIM (Gantikan Create)
@router.post("/claim", response_model=DeviceResponse)
@limiter.limit("10/minute")
def claim_device(
    request: Request,
    device_in: DeviceClaim, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    User memindai QR Code (MAC Address) untuk mengklaim alat pabrik.
    """
    logger.info(f"User {current_user.email} mencoba klaim device MAC: {device_in.mac_address}")
    
    # Cari Device di Database Pabrik
    device = db.query(Device).filter(Device.mac_address == device_in.mac_address).first()

    # VALIDASI A: Barang Ghoib (Hacker ngasal masukin MAC)
    if not device:
        logger.warning(f"Klaim GAGAL - MAC tidak terdaftar: {device_in.mac_address} oleh {current_user.email}")
        raise HTTPException(
            status_code=404, 
            detail="Device tidak dikenali! Pastikan Anda memindai QR Code produk asli."
        )

    # VALIDASI B: Barang Bekas (Sudah ada tuannya)
    if device.user_id is not None:
        logger.warning(f"Klaim GAGAL - Device sudah diklaim: {device_in.mac_address} oleh {current_user.email}")
        raise HTTPException(
            status_code=400, 
            detail="Device ini sudah diklaim oleh pengguna lain!"
        )

    # PROSES SAH KEPEMILIKAN
    device.user_id = current_user.id
    device.name = device_in.name 
    
    db.commit()
    db.refresh(device)
    
    logger.info(f"Klaim SUKSES - Device {device.mac_address} diklaim oleh {current_user.email} dengan nama '{device_in.name}'")
    return device

# 2. LIHAT DEVICE SAYA
@router.get("/", response_model=List[DeviceResponse])
@limiter.limit("30/minute")
def read_my_devices(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    devices = db.query(Device).filter(Device.user_id == current_user.id).all()
    logger.debug(f"User {current_user.email} mengambil list {len(devices)} device")
    return devices

# 2.5 BARU: LIHAT DEVICE YANG BELUM DIKLAIM (KHUSUS ADMIN)
@router.get("/unclaimed", response_model=List[DeviceResponse])
@limiter.limit("30/minute")
def get_unclaimed_devices(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Mengambil daftar semua device yang belum diklaim (user_id = NULL).
    KHUSUS ADMIN.
    """
    devices = db.query(Device).filter(Device.user_id == None).all()
    logger.debug(f"Admin {admin_user.email} mengambil list {len(devices)} unclaimed device")
    return devices

# 3. LIHAT DATA SENSOR (GRAFIK)
@router.get("/{device_id}/logs", response_model=List[LogResponse])
@limiter.limit("60/minute")
def read_device_logs(
    request: Request,
    device_id: UUID,
    limit: int = 20, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Batasi limit agar tidak bisa dump seluruh tabel
    limit = min(limit, 100)
    # Pastikan user cuma bisa liat data kandangnya sendiri
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == current_user.id).first()
    if not device:
        logger.warning(f"Akses logs DITOLAK - device_id: {device_id} oleh {current_user.email}")
        raise HTTPException(status_code=404, detail="Device tidak ditemukan akses ditolak")

    logs = db.query(SensorLog)\
        .filter(SensorLog.device_id == device_id)\
        .order_by(SensorLog.timestamp.desc())\
        .limit(limit)\
        .all()
    
    logger.debug(f"User {current_user.email} mengambil {len(logs)} logs dari device {device.name}")
    return logs

@router.post("/{device_id}/control")
@limiter.limit("30/minute")
def control_device(
    request: Request,
    device_id: UUID,
    command: DeviceControl, # Pake schema yang baru kita buat
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} mengirim kontrol ke device_id: {device_id}, component: {command.component}, state: {command.state}")
    
    # 1. Cek Kepemilikan (SECURITY CHECK)
    # Jangan sampe orang lain iseng matiin kipas lo!
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == current_user.id).first()
    
    if not device:
        logger.warning(f"Kontrol DITOLAK - device_id: {device_id} bukan milik {current_user.email}")
        raise HTTPException(status_code=404, detail="Device tidak ditemukan atau akses ditolak")

    # 2. Kirim perintah via shared MQTT client
    try:
        publish_control(device.mac_address, command.component, command.state)
        
        logger.info(f"Kontrol SUKSES - {command.component} {'ON' if command.state else 'OFF'} ke {device.name} (MAC: {device.mac_address})")
        return {"status": "success", "message": f"Perintah {command.component} dikirim ke {device.name}"}

    except Exception as e:
        logger.error(f"Kontrol GAGAL - MQTT Error untuk device {device.name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Gagal mengirim perintah ke device. Silakan coba lagi.")
    
@router.get("/{device_id}/alerts", response_model=List[LogResponse])
@limiter.limit("60/minute")
def get_device_alerts(
    request: Request,
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menampilkan daftar riwayat kondisi bahaya di kandang.
    """
    # Security Check: Pastikan device milik user yang login
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == current_user.id).first()
    if not device:
        logger.warning(f"Akses alerts DITOLAK - device_id: {device_id} oleh {current_user.email}")
        raise HTTPException(status_code=404, detail="Device tidak ditemukan atau akses ditolak")

    alerts = db.query(SensorLog)\
        .filter(
            SensorLog.device_id == device_id, 
            SensorLog.is_alert == True # Cuma ambil yang bahaya
        )\
        .order_by(SensorLog.timestamp.desc())\
        .limit(10)\
        .all()
    
    logger.debug(f"User {current_user.email} mengambil {len(alerts)} alerts dari device {device.name}")
    return alerts


# ==========================================
# 4. STATISTIK RATA-RATA SUHU HARIAN
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
    """
    Mengambil statistik rata-rata suhu harian untuk device tertentu.
    
    Data di-agregasi per hari dari tabel sensor_logs, meliputi:
    - Rata-rata, minimum, dan maksimum suhu
    - Rata-rata kelembaban dan amonia
    - Jumlah data point (pembacaan sensor)
    - Jumlah alert yang terpicu
    
    **Query Parameter:**
    - `days`: Jumlah hari ke belakang dari hari ini (default: 7, max: 90)
    
    **Contoh:** `GET /devices/{id}/stats/daily?days=30` → statistik 30 hari terakhir
    """
    logger.info(f"User {current_user.email} mengambil statistik harian device_id: {device_id}, days: {days}")
    
    # =============================================
    # 1. SECURITY CHECK - Pastikan device milik user
    # =============================================
    device = db.query(Device).filter(
        Device.id == device_id, 
        Device.user_id == current_user.id
    ).first()
    
    if not device:
        logger.warning(f"Akses stats DITOLAK - device_id: {device_id} oleh {current_user.email}")
        raise HTTPException(
            status_code=404, 
            detail="Device tidak ditemukan atau akses ditolak"
        )

    # =============================================
    # 2. HITUNG RENTANG TANGGAL
    # =============================================
    # Pakai UTC supaya konsisten dengan timestamp di database
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)  # -1 karena hari ini ikut dihitung
    
    # Konversi ke datetime untuk filter query (awal hari start_date 00:00:00 UTC)
    start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)

    # =============================================
    # 3. QUERY AGREGASI PER HARI
    # =============================================
    # Gunakan func.date() untuk extract tanggal dari kolom timestamp
    # PostgreSQL: DATE(timestamp) → '2026-01-15'
    #
    # Query SQL yang dihasilkan kurang lebih:
    # SELECT 
    #     DATE(timestamp) as log_date,
    #     AVG(temperature), MIN(temperature), MAX(temperature),
    #     AVG(humidity), AVG(ammonia),
    #     COUNT(*),
    #     SUM(CASE WHEN is_alert THEN 1 ELSE 0 END)
    # FROM sensor_logs
    # WHERE device_id = :id AND timestamp >= :start
    # GROUP BY DATE(timestamp)
    # ORDER BY log_date ASC
    
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
    ).group_by(
        log_date
    ).order_by(
        log_date.asc()
    ).all()

    # =============================================
    # 4. TRANSFORM HASIL QUERY KE SCHEMA PYDANTIC
    # =============================================
    statistics = []
    for row in daily_stats:
        # log_date bisa berupa string "2026-04-24" (SQLite) atau date object (PostgreSQL)
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

    # =============================================
    # 5. BUNGKUS DALAM RESPONSE WRAPPER
    # =============================================
    response = DailyTemperatureStatsResponse(
        device_id=device.id,
        device_name=device.name,
        period_start=start_date,
        period_end=today,
        total_days=len(statistics),  # Jumlah hari yang BENAR-BENAR ada datanya
        statistics=statistics
    )

    logger.info(
        f"Stats SUKSES - Device '{device.name}': {len(statistics)} hari data "
        f"dari {start_date} s/d {today} untuk {current_user.email}"
    )
    return response


@router.post("/{device_id}/unclaim")
@limiter.limit("10/minute")
def unclaim_device(
    request: Request,
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Melepaskan kepemilikan device. 
    Device akan kembali menjadi 'Available' untuk diklaim orang lain.
    """
    logger.info(f"User {current_user.email} mencoba unclaim device_id: {device_id}")
    
    # 1. Cek dulu: Bener gak ini device milik user yang login?
    # Security Check: Jangan sampe user A bisa unclaim device user B!
    device = db.query(Device).filter(
        Device.id == device_id, 
        Device.user_id == current_user.id
    ).first()

    if not device:
        logger.warning(f"Unclaim DITOLAK - device_id: {device_id} bukan milik {current_user.email}")
        raise HTTPException(
            status_code=404, 
            detail="Device tidak ditemukan atau bukan milik Anda!"
        )

    old_name = device.name
    old_mac = device.mac_address
    
    # 2. Proses Unclaim (Reset ke Pengaturan Pabrik)
    device.user_id = None  # Copot User ID (Jadi NULL)
    device.name = None     # Hapus nama kandang user (Reset)
    
    # Opsional: Apakah mau hapus log history juga? 
    # Buat PKL, mending jangan dihapus biar datanya tetep ada buat laporan.
    # Tapi kalau mau privasi, log harusnya dihapus.
    
    db.commit()
    db.refresh(device)

    logger.info(f"Unclaim SUKSES - Device '{old_name}' (MAC: {old_mac}) dilepas oleh {current_user.email}")
    return {"status": "success", "message": "Device berhasil di-unclaim. Sekarang device bebas diklaim lagi."}

@router.get("/{device_id}/status")
@limiter.limit("60/minute")
def get_device_status(
    request: Request,
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cek apakah device sedang Online atau Offline menggunakan kolom last_heartbeat.
    """
    # 1. Cari alatnya
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == current_user.id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device tidak ditemukan atau akses ditolak")

    # 2. Kalau alat belum pernah ngirim heartbeat sama sekali
    if not device.last_heartbeat:
        return {
            "device_id": device_id, 
            "is_online": False, 
            "last_seen": None, 
            "message": "Belum ada koneksi dari perangkat"
        }

    # 3. Hitung selisih waktu sekarang dengan last_heartbeat
    # Pastikan pakai UTC agar tidak bentrok zona waktu server vs lokal
    now = datetime.now(timezone.utc)
    
    # Kalau last_heartbeat dari DB nggak punya info timezone (naive), kita ubah jadi UTC
    if device.last_heartbeat.tzinfo is None:
        last_heartbeat_aware = device.last_heartbeat.replace(tzinfo=timezone.utc)
    else:
        last_heartbeat_aware = device.last_heartbeat

    time_diff = now - last_heartbeat_aware
    seconds_since_last_seen = time_diff.total_seconds()

    # 4. Tentukan Online/Offline (threshold dari config)
    from app.core.config import settings
    is_online = seconds_since_last_seen <= settings.DEVICE_ONLINE_TIMEOUT_SECONDS

    return {
        "device_id": device_id,
        "is_online": is_online,
        "last_seen": last_heartbeat_aware,
        "seconds_since_last_seen": round(seconds_since_last_seen)
    }