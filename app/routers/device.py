from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.device import Device  # Model Database
from app.schemas import DeviceCreate, DeviceResponse  # Schema Validasi
from app.dependencies import get_current_user  # Satpam JWT

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

# 1. Endpoint Tambah/Klaim Device Baru
@router.post("/", response_model=DeviceResponse)
def create_device(
    device_in: DeviceCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Wajib Login!
):
    # Cek dulu, jangan-jangan device ini udah pernah diklaim orang lain?
    existing_device = db.query(Device).filter(Device.mac_address == device_in.mac_address).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Device dengan MAC Address ini sudah terdaftar!")

    # Kalau aman, simpan ke database
    new_device = Device(
        mac_address=device_in.mac_address,
        name=device_in.name,
        user_id=current_user.id  # Otomatis jadi milik yang login
    )
    
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    return new_device

# 2. Endpoint Lihat Daftar Device Milik Sendiri
@router.get("/", response_model=List[DeviceResponse])
def read_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ambil device yang user_id nya sama dengan user yang login
    my_devices = db.query(Device).filter(Device.user_id == current_user.id).all()
    return my_devices