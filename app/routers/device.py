from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.device import Device, SensorLog
from app.schemas import DeviceClaim, DeviceResponse, LogResponse
from app.dependencies import get_current_user

import json
import paho.mqtt.client as mqtt
from app.core.config import settings
from app.schemas.device import DeviceControl


router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

# 1. FITUR KLAIM (Gantikan Create)
@router.post("/claim", response_model=DeviceResponse)
def claim_device(
    device_in: DeviceClaim, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    User memindai QR Code (MAC Address) untuk mengklaim alat pabrik.
    """
    # Cari Device di Database Pabrik
    device = db.query(Device).filter(Device.mac_address == device_in.mac_address).first()

    # VALIDASI A: Barang Ghoib (Hacker ngasal masukin MAC)
    if not device:
        raise HTTPException(
            status_code=404, 
            detail="Device tidak dikenali! Pastikan Anda memindai QR Code produk asli."
        )

    # VALIDASI B: Barang Bekas (Sudah ada tuannya)
    if device.user_id is not None:
        raise HTTPException(
            status_code=400, 
            detail="Device ini sudah diklaim oleh pengguna lain!"
        )

    # PROSES SAH KEPEMILIKAN
    device.user_id = current_user.id
    device.name = device_in.name 
    
    db.commit()
    db.refresh(device)
    return device

# 2. LIHAT DEVICE SAYA
@router.get("/", response_model=List[DeviceResponse])
def read_my_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Device).filter(Device.user_id == current_user.id).all()

# 3. LIHAT DATA SENSOR (GRAFIK)
@router.get("/{device_id}/logs", response_model=List[LogResponse])
def read_device_logs(
    device_id: str,
    limit: int = 20, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Pastikan user cuma bisa liat data kandangnya sendiri
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device tidak ditemukan akses ditolak")

    return db.query(SensorLog)\
        .filter(SensorLog.device_id == device_id)\
        .order_by(SensorLog.timestamp.desc())\
        .limit(limit)\
        .all()

@router.post("/{device_id}/control")
def control_device(
    device_id: str,
    command: DeviceControl, # Pake schema yang baru kita buat
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Cek Kepemilikan (SECURITY CHECK)
    # Jangan sampe orang lain iseng matiin kipas lo!
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == current_user.id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device tidak ditemukan atau akses ditolak")

    # 2. Siapkan Payload MQTT
    # Kita kirim JSON biar alat gampang bacanya
    mqtt_payload = {
        "component": command.component,
        "state": "ON" if command.state else "OFF"
    }
    
    # Topic tujuan: devices/{MAC_ADDRESS}/control
    # Ini standar komunikasi 2 arah yang rapi
    mqtt_topic = f"devices/{device.mac_address}/control"

    # 3. Eksekusi Publish ke MQTT Broker
    try:
        # Bikin client MQTT dadakan
        client = mqtt.Client()
        
        # Connect ke Broker (mosquitto)
        client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
        
        # Kirim Pesan!
        client.publish(mqtt_topic, json.dumps(mqtt_payload))
        
        # Putus koneksi (biar hemat resource)
        client.disconnect()
        
        return {"status": "success", "message": f"Perintah {command.component} dikirim ke {device.name}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengirim perintah MQTT: {str(e)}")
    
@router.get("/{device_id}/alerts", response_model=List[LogResponse])
def get_device_alerts(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menampilkan daftar riwayat kondisi bahaya di kandang.
    """
    return db.query(SensorLog)\
        .filter(
            SensorLog.device_id == device_id, 
            SensorLog.is_alert == True # Cuma ambil yang bahaya
        )\
        .order_by(SensorLog.timestamp.desc())\
        .limit(10)\
        .all()