import json
import logging
import time
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.device import Device, SensorLog
from app.core.config import settings
from app.core.logging_config import setup_logging
from sqlalchemy.sql import func

# Setup logging (untuk standalone worker)
setup_logging()
logger = logging.getLogger(__name__)

# Konfigurasi MQTT dari settings
MQTT_BROKER = settings.MQTT_BROKER
MQTT_PORT = settings.MQTT_PORT
MQTT_TOPIC = settings.MQTT_TOPIC

# Konfigurasi Alert Thresholds (bisa di-override via environment)
ALERT_TEMP_MAX = float(getattr(settings, 'ALERT_TEMP_MAX', 35))
ALERT_TEMP_MIN = float(getattr(settings, 'ALERT_TEMP_MIN', 20))
ALERT_AMMONIA_MAX = float(getattr(settings, 'ALERT_AMMONIA_MAX', 20))

# Batas wajar sensor (untuk validasi)
SENSOR_TEMP_MIN = -40.0
SENSOR_TEMP_MAX = 80.0
SENSOR_HUMID_MIN = 0.0
SENSOR_HUMID_MAX = 100.0
SENSOR_AMMONIA_MIN = 0.0
SENSOR_AMMONIA_MAX = 500.0

def validate_sensor_data(payload: dict) -> dict | None:
    """
    Validasi payload sensor data dari MQTT.
    Return data yang sudah di-sanitize, atau None jika tidak valid.
    """
    try:
        temp = float(payload.get("temp", 0))
        humidity = float(payload.get("humid", 0))
        ammonia = float(payload.get("ammonia", 0))
    except (TypeError, ValueError):
        return None
    
    # Cek batas wajar sensor
    if not (SENSOR_TEMP_MIN <= temp <= SENSOR_TEMP_MAX):
        return None
    if not (SENSOR_HUMID_MIN <= humidity <= SENSOR_HUMID_MAX):
        return None
    if not (SENSOR_AMMONIA_MIN <= ammonia <= SENSOR_AMMONIA_MAX):
        return None
    
    return {"temp": temp, "humidity": humidity, "ammonia": ammonia}

# Callback saat berhasil connect ke Broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Terhubung ke MQTT Broker dengan kode: {rc}")
        # Subscribe ke semua topic device (QoS 1 untuk reliabilitas)
        client.subscribe(MQTT_TOPIC, qos=1)
        logger.info(f"Sedang mendengarkan topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Gagal connect ke MQTT Broker! Kode: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback saat terputus dari broker"""
    if rc != 0:
        logger.warning(f"Terputus dari MQTT Broker secara tiba-tiba (rc={rc}). Reconnect otomatis...")

def on_message(client, userdata, msg):
    db = SessionLocal()
    try:
        raw_mac = msg.topic.split("/")[1]
        
        # Pengecekan dan format MAC Address (XX:XX:XX:XX:XX:XX)
        mac_address = raw_mac.strip().upper()
        if len(mac_address) == 12 and ":" not in mac_address:
            mac_address = ":".join(mac_address[i:i+2] for i in range(0, 12, 2))
            
        payload = json.loads(msg.payload.decode())
        
        device = db.query(Device).filter(Device.mac_address == mac_address).first()
        
        if not device:
            logger.warning(f"Unknown MAC: {mac_address} (raw: {raw_mac})")
            return
        
        # Validasi payload sensor
        sensor_data = validate_sensor_data(payload)
        if sensor_data is None:
            logger.warning(f"Data sensor tidak valid dari {device.name} (MAC: {mac_address}): {payload}")
            return
        
        temp = sensor_data["temp"]
        ammonia = sensor_data["ammonia"]
        humidity = sensor_data["humidity"]
        
        # --- LOGIKA ALERT (AMBANG BATAS CONFIGURABLE) ---
        is_alert = False
        alert_msg = ""

        if temp > ALERT_TEMP_MAX:
            is_alert = True
            alert_msg += "Suhu Terlalu Panas! "
        elif temp < ALERT_TEMP_MIN:
            is_alert = True
            alert_msg += "Suhu Terlalu Dingin! "

        if ammonia > ALERT_AMMONIA_MAX:
            is_alert = True
            alert_msg += "Kadar Amonia Berbahaya! "

        # Update heartbeat + Simpan log dalam SATU ATOMIC COMMIT
        device.last_heartbeat = func.now()
        
        new_log = SensorLog(
            device_id=device.id,
            temperature=temp,
            humidity=humidity,
            ammonia=ammonia,
            is_alert=is_alert,
            alert_message=alert_msg if is_alert else None
        )
        
        db.add(new_log)
        db.commit()  # Satu commit atomic untuk heartbeat + log

        if is_alert:
            logger.warning(f"ALERT untuk {device.name}: {alert_msg}")
        else:
            logger.info(f"Data masuk & Heartbeat updated: {device.name}")

    except json.JSONDecodeError:
        logger.error(f"Payload bukan JSON valid dari topic: {msg.topic}")
    except Exception as e:
        db.rollback()  # Rollback jika ada error
        logger.error(f"Error Worker: {e}")
    finally:
        db.close()

# Setup Client
client = mqtt.Client()

# Set credentials jika ada (untuk production)
if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
    client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    logger.info("MQTT Authentication enabled")

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Enable automatic reconnection
client.reconnect_delay_set(min_delay=1, max_delay=30)

# Loop utama dengan reconnection logic
if __name__ == "__main__":
    logger.info("MQTT Worker Starting...")
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            # loop_forever sudah handle auto-reconnect via on_disconnect
            client.loop_forever()
        except Exception as e:
            logger.error(f"Gagal connect ke broker: {e}. Retry dalam 5 detik...")
            time.sleep(5)