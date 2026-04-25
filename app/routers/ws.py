"""
WebSocket endpoint untuk real-time sensor data streaming.

Client connect ke: ws://host/api/ws/devices/{device_id}?token=JWT_TOKEN
Server poll database setiap POLL_INTERVAL detik dan kirim data terbaru.
"""

import logging
import asyncio
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.device import Device, SensorLog, DeviceAssignment
from app.core.security import verify_token
from app.core.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

# Interval polling database (detik)
POLL_INTERVAL = 3


def authenticate_ws_token(token: str, db: Session) -> User | None:
    """
    Authenticate WebSocket connection via JWT token.
    WebSocket tidak support HTTP headers, jadi token dikirim via query parameter.
    """
    if not token:
        return None

    payload = verify_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return None

    user = db.query(User).filter(User.id == user_uuid).first()
    return user


def check_device_access(device_id: UUID, user: User, db: Session) -> Device | None:
    """
    Cek apakah user punya akses ke device (untuk WebSocket).
    Logic sama dengan get_device_with_access di dependencies.py.
    """
    if user.role == UserRole.SUPER_ADMIN.value:
        return db.query(Device).filter(Device.id == device_id).first()

    if user.role == UserRole.ADMIN.value:
        return db.query(Device).filter(
            Device.id == device_id,
            Device.user_id == user.id
        ).first()

    if user.role in [UserRole.OPERATOR.value, UserRole.VIEWER.value]:
        assignment = db.query(DeviceAssignment).filter(
            DeviceAssignment.device_id == device_id,
            DeviceAssignment.user_id == user.id
        ).first()
        if assignment:
            return db.query(Device).filter(Device.id == device_id).first()

    return None


@router.websocket("/ws/devices/{device_id}")
async def websocket_device_stream(
    websocket: WebSocket,
    device_id: UUID,
    token: str = Query(default=""),
):
    """
    WebSocket endpoint untuk streaming data sensor real-time.
    
    Connect: ws://host/api/ws/devices/{device_id}?token=JWT_TOKEN
    
    Server akan mengirim data sensor terbaru setiap 3 detik:
    {
        "type": "sensor_data",
        "device_id": "...",
        "device_name": "Kandang Utara",
        "is_online": true,
        "latest": {
            "temperature": 28.5,
            "humidity": 72.0,
            "ammonia": 12.5,
            "is_alert": false,
            "timestamp": "2026-04-24T12:00:00Z"
        },
        "subscribers": 2
    }
    """
    db = SessionLocal()

    try:
        # 1. Authenticate
        user = authenticate_ws_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Token tidak valid")
            return

        # 2. Check device access
        device = check_device_access(device_id, user, db)
        if not device:
            await websocket.close(code=4003, reason="Akses ditolak")
            return

        # 3. Connect
        device_id_str = str(device_id)
        await ws_manager.connect(device_id_str, websocket)

        logger.info(f"WS stream started: {user.email} -> device {device.name}")

        # 4. Track last sent log ID to avoid sending duplicates
        last_log_id = 0

        # 5. Polling loop
        while True:
            try:
                # Poll database untuk data terbaru
                db.expire_all()  # Force refresh dari DB

                # Get latest sensor log
                latest_log = db.query(SensorLog).filter(
                    SensorLog.device_id == device_id
                ).order_by(SensorLog.timestamp.desc()).first()

                # Refresh device untuk heartbeat terbaru
                device = db.query(Device).filter(Device.id == device_id).first()

                # Kirim data jika ada log baru
                if latest_log and latest_log.id != last_log_id:
                    last_log_id = latest_log.id

                    from datetime import datetime, timezone, timedelta
                    from app.core.config import settings

                    # Hitung is_online
                    is_online = False
                    if device and device.last_heartbeat:
                        last_hb = device.last_heartbeat
                        if last_hb.tzinfo is None:
                            last_hb = last_hb.replace(tzinfo=timezone.utc)
                        diff = datetime.now(timezone.utc) - last_hb
                        is_online = diff.total_seconds() <= settings.DEVICE_ONLINE_TIMEOUT_SECONDS

                    data = {
                        "type": "sensor_data",
                        "device_id": str(device_id),
                        "device_name": device.name if device else None,
                        "is_online": is_online,
                        "latest": {
                            "id": latest_log.id,
                            "temperature": latest_log.temperature,
                            "humidity": latest_log.humidity,
                            "ammonia": latest_log.ammonia,
                            "is_alert": latest_log.is_alert,
                            "alert_message": latest_log.alert_message,
                            "timestamp": latest_log.timestamp.isoformat() if latest_log.timestamp else None,
                        },
                        "subscribers": ws_manager.get_subscriber_count(device_id_str),
                    }

                    await ws_manager.broadcast(device_id_str, data)

                # Tunggu sebelum poll berikutnya
                await asyncio.sleep(POLL_INTERVAL)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WS polling error: {e}")
                await asyncio.sleep(POLL_INTERVAL)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WS error: {e}")
    finally:
        ws_manager.disconnect(str(device_id), websocket)
        db.close()
        logger.info(f"WS stream ended: device {device_id}")
