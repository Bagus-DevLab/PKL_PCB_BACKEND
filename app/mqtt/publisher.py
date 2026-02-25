"""
Shared MQTT client untuk publishing perintah kontrol.
Menggunakan persistent connection agar tidak perlu connect/disconnect setiap request.
"""

import json
import logging
import paho.mqtt.client as mqtt
from app.core.config import settings

logger = logging.getLogger(__name__)

# Singleton MQTT client untuk publish
_mqtt_client: mqtt.Client | None = None


def _get_mqtt_client() -> mqtt.Client:
    """
    Mendapatkan atau membuat persistent MQTT client.
    Thread-safe karena paho-mqtt handle locking internal.
    """
    global _mqtt_client
    
    if _mqtt_client is None or not _mqtt_client.is_connected():
        _mqtt_client = mqtt.Client()
        
        # Set credentials jika ada
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            _mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        
        # Enable auto-reconnect
        _mqtt_client.reconnect_delay_set(min_delay=1, max_delay=10)
        
        try:
            _mqtt_client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
            # Start background network loop (non-blocking)
            _mqtt_client.loop_start()
            logger.info("MQTT Publisher client terhubung")
        except Exception as e:
            logger.error(f"Gagal connect MQTT Publisher: {e}")
            _mqtt_client = None
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
    
    mqtt_topic = f"devices/{mac_address}/control"
    
    # Publish dengan QoS 1 agar lebih reliable
    result = client.publish(mqtt_topic, json.dumps(mqtt_payload), qos=1)
    result.wait_for_publish(timeout=5)
    
    logger.info(f"MQTT Published ke {mqtt_topic}: {mqtt_payload}")
