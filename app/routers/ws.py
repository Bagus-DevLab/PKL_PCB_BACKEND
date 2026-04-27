"""
WebSocket endpoint untuk real-time sensor data streaming.

Client connect ke: ws://host/api/ws/devices/{device_id}?token=JWT_TOKEN
Server poll database setiap POLL_INTERVAL detik dan kirim data terbaru.

CATATAN KEAMANAN: JWT token dikirim via query parameter karena WebSocket
tidak support custom HTTP headers. Token akan terlihat di server logs
dan browser history. Pertimbangkan short-lived token untuk WebSocket.
"""

import logging
import asyncio
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.device import Device, SensorLog, DeviceAssignment
from app.core.security import verify_token
from app.core.config import settings
from app.core.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

POLL_INTERVAL = 3

# Sentinel value: device was deleted from DB
_DEVICE_DELETED = {"_deleted": True}


def _authenticate_ws(token: str, db: Session) -> User | None:
    """Authenticate WebSocket via JWT token dari query parameter."""
    if not token:
        return None
    payload = verify_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return None
    user = db.query(User).filter(User.id == user_uuid).first()
    if user and not user.is_active:
        return None
    return user


def _check_access(device_id: UUID, user: User, db: Session) -> Device | None:
    """Cek akses user ke device."""
    if user.role == UserRole.SUPER_ADMIN.value:
        return db.query(Device).filter(Device.id == device_id).first()
    if user.role == UserRole.ADMIN.value:
        return db.query(Device).filter(Device.id == device_id, Device.user_id == user.id).first()
    if user.role in [UserRole.OPERATOR.value, UserRole.VIEWER.value]:
        assignment = db.query(DeviceAssignment).filter(
            DeviceAssignment.device_id == device_id,
            DeviceAssignment.user_id == user.id
        ).first()
        if assignment:
            return db.query(Device).filter(Device.id == device_id).first()
    return None


def _poll_device_data(device_id: UUID) -> dict | None:
    """
    Poll database untuk data sensor terbaru.
    Buat session baru per poll cycle agar tidak hold connection pool.

    Returns:
        dict with sensor data — new data available
        None — no new data (device exists but no logs yet)
        _DEVICE_DELETED — device no longer exists in DB
    """
    db = SessionLocal()
    try:
        # Query Device dulu untuk deteksi deletion
        device = db.query(Device).filter(Device.id == device_id).first()

        if not device:
            return _DEVICE_DELETED

        latest_log = db.query(SensorLog).filter(
            SensorLog.device_id == device_id
        ).order_by(SensorLog.timestamp.desc()).first()

        if not latest_log:
            return None

        # Hitung is_online
        is_online = False
        if device.last_heartbeat:
            last_hb = device.last_heartbeat
            if last_hb.tzinfo is None:
                last_hb = last_hb.replace(tzinfo=timezone.utc)
            diff = datetime.now(timezone.utc) - last_hb
            is_online = diff.total_seconds() <= settings.DEVICE_ONLINE_TIMEOUT_SECONDS

        return {
            "log_id": latest_log.id,
            "type": "sensor_data",
            "device_id": str(device_id),
            "device_name": device.name,
            "is_online": is_online,
            "latest": {
                "id": latest_log.id,
                "temperature": latest_log.temperature,
                "humidity": latest_log.humidity,
                "ammonia": latest_log.ammonia,
                "light_level": latest_log.light_level,
                "is_alert": latest_log.is_alert,
                "alert_message": latest_log.alert_message,
                "timestamp": latest_log.timestamp.isoformat() if latest_log.timestamp else None,
            },
        }
    except Exception as e:
        logger.error(f"WS poll error: {e}")
        return None
    finally:
        db.close()


@router.websocket("/ws/devices/{device_id}")
async def websocket_device_stream(
    websocket: WebSocket,
    device_id: UUID,
    token: str = Query(default=""),
):
    """
    WebSocket endpoint untuk streaming data sensor real-time.
    Connect: ws://host/api/ws/devices/{device_id}?token=JWT_TOKEN
    """
    # HARUS accept dulu sebelum bisa close dengan error code
    await websocket.accept()

    # Authenticate dengan session terpisah (short-lived)
    db = SessionLocal()
    try:
        user = _authenticate_ws(token, db)
        if not user:
            await websocket.close(code=4001, reason="Token tidak valid")
            return

        device = _check_access(device_id, user, db)
        if not device:
            await websocket.close(code=4003, reason="Akses ditolak")
            return

        user_email = user.email
        device_name = device.name
    finally:
        db.close()  # Close auth session segera

    # Register connection
    device_id_str = str(device_id)
    ws_manager.register(device_id_str, websocket)
    logger.info(f"WS stream started: {user_email} -> device {device_name}")

    last_log_id = 0

    try:
        while True:
            try:
                data = await asyncio.to_thread(_poll_device_data, device_id)

                # Device dihapus dari DB — tutup WebSocket dengan kode khusus
                if data is _DEVICE_DELETED:
                    logger.info(f"Device {device_id} deleted, closing WS for {user_email}")
                    try:
                        await websocket.close(code=4004, reason="Device telah dihapus")
                    except Exception:
                        pass
                    break

                if data and data["log_id"] != last_log_id:
                    last_log_id = data["log_id"]
                    data["subscribers"] = ws_manager.get_subscriber_count(device_id_str)
                    del data["log_id"]
                    await websocket.send_json(data)

                await asyncio.sleep(POLL_INTERVAL)

            except WebSocketDisconnect:
                break
            except Exception as e:
                # Semua exception lain (RuntimeError, ConnectionResetError, dll)
                # berarti koneksi sudah mati — BREAK, jangan lanjut polling.
                logger.warning(f"WS connection lost for {user_email}: {e}")
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WS error: {e}")
    finally:
        ws_manager.disconnect(device_id_str, websocket)
        logger.info(f"WS stream ended: device {device_id}")
