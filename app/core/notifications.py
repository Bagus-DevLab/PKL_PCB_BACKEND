"""
Push notification sender via Firebase Cloud Messaging (FCM).
Digunakan oleh MQTT worker untuk mengirim alert ke user.
"""

import logging
from typing import List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def send_alert_notification(
    device_name: str,
    device_id: str,
    alert_message: str,
    temperature: float,
    humidity: float,
    ammonia: float,
    db: Session,
):
    """
    Kirim push notification ke semua user yang terkait dengan device.
    
    User yang menerima notifikasi:
    1. Device owner (admin yang claim device)
    2. Operator yang di-assign ke device
    
    Viewer TIDAK menerima notifikasi (read-only).
    """
    from app.models.device import Device, DeviceAssignment
    from app.models.user import FcmToken, UserRole

    try:
        from firebase_admin import messaging
    except ImportError:
        logger.warning("Firebase Admin SDK tidak tersedia. Push notification dilewati.")
        return

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

    # Ambil FCM tokens untuk semua user terkait
    tokens = db.query(FcmToken.token).filter(
        FcmToken.user_id.in_(user_ids)
    ).all()

    fcm_tokens = [t[0] for t in tokens]

    if not fcm_tokens:
        logger.debug(f"Tidak ada FCM token untuk device {device_name}. Notifikasi dilewati.")
        return

    # Buat notification message
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

    # Kirim ke semua token sekaligus (batch)
    message = messaging.MulticastMessage(
        notification=notification,
        data=data_payload,
        tokens=fcm_tokens,
    )

    try:
        response = messaging.send_each_for_multicast(message)

        success_count = response.success_count
        failure_count = response.failure_count

        logger.info(
            f"FCM notification sent for {device_name}: "
            f"{success_count} success, {failure_count} failed, "
            f"{len(fcm_tokens)} tokens"
        )

        # Hapus token yang invalid (expired/unregistered)
        if failure_count > 0:
            for i, send_response in enumerate(response.responses):
                if send_response.exception:
                    error_code = getattr(send_response.exception, 'code', None)
                    if error_code in ['NOT_FOUND', 'UNREGISTERED', 'INVALID_ARGUMENT']:
                        invalid_token = fcm_tokens[i]
                        db.query(FcmToken).filter(FcmToken.token == invalid_token).delete()
                        logger.info(f"FCM token invalid dihapus: {invalid_token[:20]}...")

            db.commit()

    except Exception as e:
        logger.error(f"FCM send error: {e}")
