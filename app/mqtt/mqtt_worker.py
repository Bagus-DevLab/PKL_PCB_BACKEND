import os
import json
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.device import Device, SensorLog

# Konfigurasi MQTT
# Ingat: Di dalam Docker network, hostnamenya adalah nama service ("mosquitto" atau "pcb_pkl_mosquitto")
MQTT_BROKER = "mosquitto" 
MQTT_PORT = 1883
MQTT_TOPIC = "devices/+/data" # Tanda '+' itu Wildcard. Artinya kita dengerin SEMUA device.

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

# Callback saat ada pesan masuk (DAGINGNYA DISINI)
def on_message(client, userdata, msg):
    print(f"📩 Pesan masuk di topic: {msg.topic}")
    
    db = SessionLocal()
    try:
        # 1. Parsing Topic buat dapet MAC Address
        # Format topic: devices/{mac_address}/data
        topic_parts = msg.topic.split("/")
        mac_address = topic_parts[1]
        
        # 2. Parsing Data JSON dari ESP32
        payload = json.loads(msg.payload.decode())
        print(f"   Data: {payload}")
        
        # 3. Cari Device di Database
        device = db.query(Device).filter(Device.mac_address == mac_address).first()
        
        if not device:
            print(f"⚠️ Device dengan MAC {mac_address} tidak ditemukan di database. Data diabaikan.")
            return

        # 4. Simpan ke Sensor Log (Big Data Ingestion)
        new_log = SensorLog(
            device_id=device.id,
            temperature=payload.get("temp", 0.0),
            humidity=payload.get("humid", 0.0),
            ammonia=payload.get("ammonia", 0.0)
        )
        
        db.add(new_log)
        db.commit()
        print(f"💾 Data tersimpan untuk Device: {device.name}")

    except Exception as e:
        print(f"❌ Error memproses data: {e}")
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