import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.models.device import Device, SensorLog
from app.schemas import DeviceClaim, DeviceResponse, LogResponse
from app.dependencies import get_current_user, get_current_admin

import json
import paho.mqtt.client as mqtt
from app.core.config import settings
from app.schemas.device import DeviceControl
from app.core.request_context import get_request_id
from app.mqtt.publisher import publish_control

logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

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