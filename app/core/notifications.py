"""
Push notification sender via Firebase Cloud Messaging (FCM).
Digunakan oleh MQTT worker untuk mengirim alert ke user.

Menggunakan DB session sendiri (bukan shared) agar tidak
mengganggu transaction caller jika terjadi error.
"""

import logging
import time

logger = logging.getLogger(__name__)

# Cooldown: max 1 notifikasi per device per 5 menit.
# Key: device_id (str), Value: time.monotonic() saat terakhir kirim.
NOTIFICATION_COOLDOWN_SECONDS = 300
_notification_cooldown: dict[str, float] = {}


def send_alert_notification(
    device_name: str,
    device_id: str,
    alert_message: str,
    temperature: float,
    humidity: float,
    ammonia: float,
):
    """
    Kirim push notification ke semua user yang terkait dengan device.
    
    Menggunakan DB session sendiri — aman dipanggil dari MQTT worker
    tanpa mengganggu session caller.
    
    User yang menerima notifikasi:
    1. Device owner (admin yang claim device)
    2. Operator yang di-assign ke device
    """
    from app.database import SessionLocal
    from app.models.device import Device, DeviceAssignment
    from app.models.user import FcmToken, UserRole

    try:
        from firebase_admin import messaging
    except ImportError:
        logger.warning("Firebase Admin SDK tidak tersedia. Push notification dilewati.")
        return

    # Cooldown check: skip jika notifikasi terakhir < 5 menit lalu
    now = time.monotonic()
    last_sent = _notification_cooldown.get(device_id)
    if last_sent is not None and (now - last_sent) < NOTIFICATION_COOLDOWN_SECONDS:
        logger.debug(
            f"Notification cooldown active for device {device_name} "
            f"({int(NOTIFICATION_COOLDOWN_SECONDS - (now - last_sent))}s remaining)"
        )
        return

    db = None
    try:
        db = SessionLocal()

        # Cari device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return

        # Kumpulkan user_ids yang perlu dinotifikasi
        user_ids = set()

        # 1. Device owner
        if device.user_id:
            user_ids.add(device.user_id)

        # 2. Operator yang di-assign (bukan viewer)
        assignments = db.query(DeviceAssignment).filter(
            DeviceAssignment.device_id == device_id,
            DeviceAssignment.role == UserRole.OPERATOR.value,
        ).all()

        for assignment in assignments:
            user_ids.add(assignment.user_id)

        if not user_ids:
            return

        # Ambil FCM tokens
        tokens = db.query(FcmToken.token).filter(
            FcmToken.user_id.in_(user_ids)
        ).all()

        fcm_tokens = [t[0] for t in tokens]

        if not fcm_tokens:
            logger.debug(f"Tidak ada FCM token untuk device {device_name}.")
            return

        # Buat notification
        notification = messaging.Notification(
            title=f"Alert: {device_name}",
            body=alert_message,
        )

        data_payload = {
            "device_id": str(device_id),
            "device_name": device_name or "",
            "temperature": str(temperature),
            "humidity": str(humidity),
            "ammonia": str(ammonia),
            "alert_message": alert_message,
            "type": "sensor_alert",
        }

        message = messaging.MulticastMessage(
            notification=notification,
            data=data_payload,
            tokens=fcm_tokens,
        )

        response = messaging.send_each_for_multicast(message)

        logger.info(
            f"FCM sent for {device_name}: "
            f"{response.success_count} success, {response.failure_count} failed"
        )

        # Update cooldown timestamp setelah berhasil kirim
        _notification_cooldown[device_id] = time.monotonic()

        # Hapus token yang invalid
        if response.failure_count > 0:
            for i, send_response in enumerate(response.responses):
                if send_response.exception:
                    error_code = getattr(send_response.exception, 'code', None)
                    if error_code in ['NOT_FOUND', 'UNREGISTERED', 'INVALID_ARGUMENT']:
                        invalid_token = fcm_tokens[i]
                        db.query(FcmToken).filter(FcmToken.token == invalid_token).delete()
                        logger.info(f"FCM token invalid dihapus: {invalid_token[:20]}...")
            db.commit()

    except Exception as e:
        logger.error(f"FCM notification error: {e}")
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
    finally:
        if db is not None:
            db.close()
