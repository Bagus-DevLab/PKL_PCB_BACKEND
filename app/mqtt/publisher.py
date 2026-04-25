"""
Shared MQTT client untuk publishing perintah kontrol.
Menggunakan persistent connection dengan thread-safe singleton.
"""

import json
import logging
import os
import threading
import paho.mqtt.client as mqtt
from app.core.config import settings

logger = logging.getLogger(__name__)

# Thread-safe singleton
_mqtt_client: mqtt.Client | None = None
_mqtt_lock = threading.Lock()
_mqtt_initialized = False


def _create_mqtt_client() -> mqtt.Client:
    """Buat MQTT client baru dengan paho-mqtt v2 API."""
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"pcb_publisher_{os.getpid()}",
    )

    # Set credentials jika ada
    if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
        client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

    # Enable auto-reconnect
    client.reconnect_delay_set(min_delay=1, max_delay=10)

    # Callbacks
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info("MQTT Publisher terhubung ke broker")
        else:
            logger.error(f"MQTT Publisher gagal connect: {reason_code}")

    def on_disconnect(client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            logger.warning(f"MQTT Publisher terputus (rc={reason_code}). Auto-reconnect...")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    return client


def _get_mqtt_client() -> mqtt.Client:
    """
    Mendapatkan persistent MQTT client (thread-safe singleton).
    Client dibuat sekali dan loop_start() handle reconnection otomatis.
    """
    global _mqtt_client, _mqtt_initialized

    # Fast path: client sudah ada dan initialized
    if _mqtt_initialized and _mqtt_client is not None:
        return _mqtt_client

    # Slow path: perlu inisialisasi (thread-safe)
    with _mqtt_lock:
        # Double-check setelah acquire lock
        if _mqtt_initialized and _mqtt_client is not None:
            return _mqtt_client

        _mqtt_client = _create_mqtt_client()

        try:
            _mqtt_client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
            _mqtt_client.loop_start()
            _mqtt_initialized = True
            logger.info("MQTT Publisher client initialized")
        except Exception as e:
            logger.error(f"Gagal connect MQTT Publisher: {e}")
            _mqtt_client = None
            _mqtt_initialized = False
            raise

    return _mqtt_client


def publish_control(mac_address: str, component: str, state: bool) -> None:
    """
    Publish perintah kontrol ke device via MQTT.

    Args:
        mac_address: MAC address device tujuan
        component: Komponen yang dikontrol (kipas, lampu, dll)
        state: True = ON, False = OFF
    """
    client = _get_mqtt_client()

    mqtt_payload = {
        "component": component,
        "state": "ON" if state else "OFF"
    }

    # Format MAC address untuk ESP32 (hilangkan titik dua)
    formatted_mac = mac_address.replace(":", "").upper()
    mqtt_topic = f"devices/{formatted_mac}/control"

    # Publish dengan QoS 1 agar reliable
    result = client.publish(mqtt_topic, json.dumps(mqtt_payload), qos=1)
    result.wait_for_publish(timeout=5)

    logger.info(f"MQTT Published ke {mqtt_topic}: {mqtt_payload}")
