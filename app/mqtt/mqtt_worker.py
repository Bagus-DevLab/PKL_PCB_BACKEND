import json
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.device import Device, SensorLog
from app.core.config import settings

# Konfigurasi MQTT dari settings
MQTT_BROKER = settings.MQTT_BROKER
MQTT_PORT = settings.MQTT_PORT
MQTT_TOPIC = settings.MQTT_TOPIC

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Callback saat berhasil connect ke Broker
def on_connect(client, userdata, flags, rc):
    print(f"✅ Terhubung ke MQTT Broker dengan kode: {rc}")
    # Subscribe ke semua topic device
    client.subscribe(MQTT_TOPIC)
    print(f"📡 Sedang mendengarkan topic: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    db = SessionLocal()
    try:
        mac_address = msg.topic.split("/")[1]
        payload = json.loads(msg.payload.decode())
        
        device = db.query(Device).filter(Device.mac_address == mac_address).first()
        
        if device:
            temp = payload.get("temp", 0)
            ammonia = payload.get("ammonia", 0)
            
            # --- LOGIKA ALERT (AMBANG BATAS) ---
            is_alert = False
            alert_msg = ""

            if temp > 35:
                is_alert = True
                alert_msg += "Suhu Terlalu Panas! "
            elif temp < 20:
                is_alert = True
                alert_msg += "Suhu Terlalu Dingin! "

            if ammonia > 20:
                is_alert = True
                alert_msg += "Kadar Amonia Berbahaya! "

            # Simpan ke Database
            new_log = SensorLog(
                device_id=device.id,
                temperature=temp,
                humidity=payload.get("humid", 0),
                ammonia=ammonia,
                is_alert=is_alert,
                alert_message=alert_msg if is_alert else None
            )
            
            db.add(new_log)
            db.commit()

            if is_alert:
                print(f"🚨 ALERT untuk {device.name}: {alert_msg}")
            else:
                print(f"✅ Data normal untuk {device.name}")

    except Exception as e:
        print(f"❌ Error Worker: {e}")
    finally:
        db.close()

# Setup Client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Loop utama
if __name__ == "__main__":
    print("🚀 MQTT Worker Starting...")
    try:
        # Connect ke broker
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        # Loop forever (Blocking)
        client.loop_forever()
    except Exception as e:
        print(f"🔥 Gagal connect ke broker: {e}")