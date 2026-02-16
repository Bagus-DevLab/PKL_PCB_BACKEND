# 🐔 Smart Coop IoT Backend (Sistem Kandang Ayam Pintar)

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)
![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-3C5280?style=for-the-badge&logo=eclipse-mosquitto)

Backend server untuk sistem monitoring dan controlling kandang ayam berbasis IoT. Project ini dibuat untuk keperluan **PKL / Skripsi**. Menggunakan arsitektur **Microservices** sederhana dengan Docker.

---

## 🚀 Fitur Utama

### 1. 🔐 Keamanan & Autentikasi
- **Google OAuth Login:** Login menggunakan akun Google.
- **JWT Protection:** Semua endpoint diamankan dengan Token JWT.
- **Rate Limiting:** Proteksi terhadap DDoS dan brute force attack.
- **CORS Middleware:** Kontrol akses dari frontend berbeda domain.

### 2. 🏭 Manajemen Device (Whitelist System)
- **Factory Registration:** Device harus didaftarkan dulu oleh "Pabrik" di database (Pre-seeding).
- **Secure Claiming:** User mengklaim device dengan memindai QR Code (MAC Address).
- **Anti-Fake Device:** Mencegah user mendaftarkan MAC Address sembarangan.
- **Unclaim:** Fitur untuk melepas kepemilikan device (Reset ke pengaturan pabrik).

### 3. 📡 Real-time Monitoring & Alerting
- **MQTT Ingestion:** Menerima data sensor (Suhu, Kelembapan, Amonia) secara real-time via Mosquitto.
- **MQTT Authentication:** Mendukung username/password untuk keamanan broker.
- **Smart Alerting:** Mendeteksi bahaya otomatis dan menyimpan flag `is_alert`.
    - 🚨 *Suhu > 35°C* (Panas)
    - ❄️ *Suhu < 20°C* (Dingin)
    - ☠️ *Amonia > 20 ppm* (Beracun)
- **Heartbeat Monitor:** Mendeteksi status **ONLINE/OFFLINE** device berdasarkan waktu kirim data terakhir (Threshold: 5 menit).

### 4. 🎮 Remote Control (2-Arah)
- Mengontrol perangkat keras (Kipas, Lampu, Pompa) dari aplikasi via API.
- Backend meneruskan perintah ke Device melalui topik MQTT.

### 5. 📊 Logging & Monitoring
- **Rotating Log Files:** Log tersimpan di `logs/backend.log` dengan rotasi otomatis.
- **Structured Logging:** Format log yang konsisten untuk debugging.
- **Health Check:** Endpoint `/` untuk monitoring status server dan database.

---

## 🛠️ Tech Stack & Arsitektur

| Category | Technology |
|----------|------------|
| **Language** | Python 3.11 |
| **Framework** | FastAPI 0.115.0 |
| **Database** | PostgreSQL 15 |
| **Message Broker** | Eclipse Mosquitto 2.x |
| **ORM** | SQLAlchemy 2.0 |
| **Validation** | Pydantic 2.x |
| **Rate Limiting** | SlowAPI |
| **Container** | Docker & Docker Compose |
| **Testing** | pytest, httpx |

---

## ⚙️ Cara Install & Menjalankan

### 1. Clone Repository
```bash
git clone https://github.com/Bagus-DevLab/PKL_PCB_BACKEND.git
cd pkl-pcb
```

### 2. Konfigurasi Environment
Buat file `.env` di root folder (copy dari `.env.example`).

```env
# ===========================================
# PKL PCB IoT Backend - Environment Variables
# ===========================================

# Environment: development / production
ENVIRONMENT=development

# ===========================================
# Database (PostgreSQL)
# ===========================================
POSTGRES_USER=iot_user
POSTGRES_PASSWORD=supersecret
POSTGRES_DB=iot_db
DATABASE_URL=postgresql://iot_user:supersecret@postgres:5432/iot_db

# ===========================================
# JWT Authentication
# ===========================================
SECRET_KEY=ganti_dengan_random_string_panjang_dan_rahasia
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 hari

# ===========================================
# Google OAuth (Dapat dari Google Cloud Console)
# ===========================================
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
BASE_URL=http://localhost:8000

# ===========================================
# MQTT (Mosquitto)
# ===========================================
MQTT_BROKER=mosquitto
MQTT_PORT=1883
MQTT_TOPIC=devices/+/data
MQTT_USERNAME=
MQTT_PASSWORD=

# ===========================================
# CORS (Frontend Origins)
# ===========================================
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

### 3. Jalankan dengan Docker

**Development (dengan hot-reload):**
```bash
docker compose up -d --build
```

**Production (tanpa hot-reload, dengan workers):**
```bash
docker compose -f docker-compose.yml up -d --build
```

### 4. ⚠️ PENTING: Seeding Data Pabrik (Initial Setup)
Karena sistem menggunakan Whitelist, device tidak bisa daftar sendiri. Anda harus memasukkan data awal sebagai "Pabrik".

**Opsi A: Menggunakan Docker Exec (Satu per satu)**
```bash
# Mendaftarkan device dengan MAC AA:BB:CC:11:22:33
docker exec -it pcb_pkl_postgres psql -U iot_user -d iot_db -c \
  "INSERT INTO devices (id, mac_address, name, user_id) VALUES (gen_random_uuid(), 'AA:BB:CC:11:22:33', 'Stok Gudang A1', NULL);"
```

**Opsi B: Masuk ke PostgreSQL Shell (Bulk Insert)**
```bash
# Masuk ke shell PostgreSQL
docker exec -it pcb_pkl_postgres psql -U iot_user -d iot_db

# Kemudian jalankan SQL berikut:
INSERT INTO devices (id, mac_address, name, user_id) VALUES 
  (gen_random_uuid(), 'AA:BB:CC:11:22:33', 'Stok Gudang A1', NULL),
  (gen_random_uuid(), 'AA:BB:CC:11:22:44', 'Stok Gudang A2', NULL),
  (gen_random_uuid(), 'AA:BB:CC:11:22:55', 'Stok Gudang A3', NULL);

# Verifikasi data
SELECT id, mac_address, name, user_id FROM devices;

# Keluar dari shell
\q
```

**Opsi C: Menggunakan Script SQL**
```bash
# Buat file seed.sql
cat > seed.sql << 'EOF'
INSERT INTO devices (id, mac_address, name, user_id) VALUES 
  (gen_random_uuid(), 'AA:BB:CC:11:22:33', 'Stok Gudang A1', NULL),
  (gen_random_uuid(), 'AA:BB:CC:11:22:44', 'Stok Gudang A2', NULL);
EOF

# Jalankan script
docker exec -i pcb_pkl_postgres psql -U iot_user -d iot_db < seed.sql
```

---

## 🔒 Setup MQTT Authentication (Opsional)

Untuk mengamankan MQTT broker agar tidak bisa diakses sembarang orang:

### 1. Buat Password File
```bash
# Install mosquitto tools di WSL/Linux
sudo apt-get install -y mosquitto

# Buat password file
mosquitto_passwd -c mosquitto/config/passwd device_user
# Masukkan password (2x)

# Fix permission
sudo chown 1883:1883 mosquitto/config/passwd
```

### 2. Edit mosquitto.conf
```properties
listener 1883
allow_anonymous false
password_file /mosquitto/config/passwd
persistence true
persistence_location /mosquitto/data/
log_dest stdout
```

### 3. Update .env
```env
MQTT_USERNAME=device_user
MQTT_PASSWORD=your_password
```

### 4. Restart
```bash
docker compose restart mosquitto backend mqtt_worker
```

---

## 📚 Dokumentasi API

Akses Swagger UI untuk dokumentasi interaktif:  
👉 **http://localhost:8000/docs**

### Endpoint Penting

| Method | Endpoint | Deskripsi | Rate Limit |
|--------|----------|-----------|------------|
| `GET` | `/` | Health check | 60/min |
| `GET` | `/auth/google/login` | Login via Google | 10/min |
| `GET` | `/users/me` | Get user profile | 30/min |
| `POST` | `/devices/claim` | Klaim device (Scan QR) | 10/min |
| `GET` | `/devices/` | List devices milik user | 30/min |
| `GET` | `/devices/{id}/logs` | History data sensor | 60/min |
| `GET` | `/devices/{id}/alerts` | Riwayat bahaya | 60/min |
| `POST` | `/devices/{id}/control` | Remote control device | 30/min |
| `POST` | `/devices/{id}/unclaim` | Lepas kepemilikan | 10/min |

---

## 🔌 Integrasi Hardware (ESP32)

### Kirim Data Sensor (Publish)
Device harus mengirim data JSON ke topik: `devices/{MAC_ADDRESS}/data`

**Format JSON:**
```json
{
  "temp": 30.5,
  "humidity": 75.0,
  "ammonia": 0.5    
}
```

### Terima Perintah Kontrol (Subscribe)
Device harus subscribe ke topik: `devices/{MAC_ADDRESS}/control`

**Format JSON yang diterima:**
```json
{
  "component": "fan",
  "state": "ON"
}
```

### Contoh Kode ESP32 (dengan Auth)
```cpp
#include <PubSubClient.h>

const char* mqtt_server = "IP_SERVER_ANDA";
const int mqtt_port = 1883;
const char* mqtt_user = "device_user";      // Sesuaikan dengan .env
const char* mqtt_pass = "your_password";    // Sesuaikan dengan .env
const char* mac_address = "AA:BB:CC:DD:EE:FF";

WiFiClient espClient;
PubSubClient client(espClient);

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32_Client", mqtt_user, mqtt_pass)) {
      // Subscribe ke topic control
      String topic = "devices/" + String(mac_address) + "/control";
      client.subscribe(topic.c_str());
    } else {
      delay(5000);
    }
  }
}

void sendSensorData(float temp, float humidity, float ammonia) {
  String topic = "devices/" + String(mac_address) + "/data";
  String payload = "{\"temp\":" + String(temp) + 
                   ",\"humidity\":" + String(humidity) + 
                   ",\"ammonia\":" + String(ammonia) + "}";
  client.publish(topic.c_str(), payload.c_str());
}
```

---

## 🐞 Debug dengan MQTTX

[MQTTX](https://mqttx.app/) adalah GUI client untuk testing MQTT.

### Setup Koneksi
| Field | Value |
|-------|-------|
| Host | `localhost` |
| Port | `1883` |
| Username | `device_user` (jika auth aktif) |
| Password | `your_password` (jika auth aktif) |

### Testing

**1. Monitor Data Sensor:**
- Subscribe ke: `devices/#` atau `devices/+/data`

**2. Simulasi Hardware (Kirim Data Test):**
- Topic: `devices/AA:BB:CC:DD:EE:FF/data`
- Payload:
```json
{"temp": 32.5, "humidity": 65, "ammonia": 15}
```

**3. Monitor Perintah Kontrol:**
- Subscribe ke: `devices/+/control`
- Trigger dari Swagger UI: `POST /devices/{id}/control`

---

## 🐛 Troubleshooting

| Problem | Solusi |
|---------|--------|
| Container tidak jalan? | `docker compose logs -f backend` untuk lihat error |
| MQTT "Not authorized"? | Cek username/password di .env dan mosquitto config |
| Data tidak masuk database? | Pastikan MAC Address sudah di-seed ke database |
| Device selalu OFFLINE? | Device harus kirim data tiap 5 menit (heartbeat) |
| Rate limit exceeded? | Tunggu 1 menit atau kurangi frekuensi request |
| CORS error di frontend? | Tambahkan origin frontend ke `CORS_ORIGINS` di .env |

### Cek Log
```bash
# Backend API
docker compose logs -f backend

# MQTT Worker
docker compose logs -f mqtt_worker

# Mosquitto Broker
docker compose logs -f mosquitto

# Semua service
docker compose logs -f
```

---

## 🚀 Deploy ke Production

### Checklist Sebelum Deploy

- [ ] Set `ENVIRONMENT=production` di `.env`
- [ ] Ganti `SECRET_KEY` dengan random string 64 karakter
- [ ] Update `BASE_URL` dengan domain production
- [ ] Update `CORS_ORIGINS` dengan domain frontend
- [ ] (Opsional) Setup MQTT Authentication
- [ ] (Opsional) Setup HTTPS dengan reverse proxy (nginx/traefik)

---

## 🧪 Unit Testing

Project ini dilengkapi dengan unit test menggunakan **pytest**.

### Struktur Test
```
tests/
├── __init__.py
├── conftest.py       # Fixtures & test database setup
├── test_security.py  # Test JWT token (8 tests)
├── test_device.py    # Test endpoint /devices (20 tests)
└── test_user.py      # Test endpoint /users & health (7 tests)
```

### Cara Menjalankan Test

```bash
# Install dependencies testing
pip install pytest pytest-asyncio httpx

# Jalankan semua test
pytest

# Dengan verbose output
pytest -v

# Jalankan test spesifik
pytest tests/test_device.py

# Dengan coverage report (opsional)
pip install pytest-cov
pytest --cov=app
```

### Test Coverage

| Module | Test Cases | Deskripsi |
|--------|------------|-----------|
| `test_security.py` | 8 | Create/verify JWT token, expired token, invalid token |
| `test_device.py` | 20 | Claim, unclaim, list devices, logs, alerts, control |
| `test_user.py` | 7 | Get current user, auth validation, health check |

**Total: 35 test cases**

---

## � Blackbox Testing (API Testing)

Blackbox testing dilakukan untuk menguji API dari perspektif pengguna tanpa melihat kode internal.

### 1. Menggunakan Swagger UI (Recommended)

Akses dokumentasi interaktif di: **http://localhost:8000/docs**

**Langkah Testing:**
1. Buka Swagger UI di browser
2. Klik endpoint yang ingin ditest
3. Klik tombol **"Try it out"**
4. Isi parameter yang diperlukan
5. Klik **"Execute"**
6. Lihat response code dan body

### 2. Menggunakan Postman

Import collection atau buat request manual:

**A. Health Check (Tanpa Auth)**
```
GET http://localhost:8000/
```

**B. Login Google OAuth**
```
GET http://localhost:8000/auth/google/login
```
*Akan redirect ke halaman login Google*

**C. Get User Profile (Dengan Auth)**
```
GET http://localhost:8000/users/me
Headers:
  Authorization: Bearer <JWT_TOKEN>
```

**D. Claim Device**
```
POST http://localhost:8000/devices/claim
Headers:
  Authorization: Bearer <JWT_TOKEN>
  Content-Type: application/json
Body:
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "name": "Kandang Ayam 1"
}
```

**E. Get My Devices**
```
GET http://localhost:8000/devices/
Headers:
  Authorization: Bearer <JWT_TOKEN>
```

**F. Control Device**
```
POST http://localhost:8000/devices/{device_id}/control
Headers:
  Authorization: Bearer <JWT_TOKEN>
  Content-Type: application/json
Body:
{
  "component": "kipas",
  "state": true
}
```

### 3. Menggunakan cURL

```bash
# Health Check
curl -X GET http://localhost:8000/

# Get User Profile (ganti TOKEN dengan JWT valid)
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer TOKEN"

# Claim Device
curl -X POST http://localhost:8000/devices/claim \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF", "name": "Kandang 1"}'

# Get My Devices
curl -X GET http://localhost:8000/devices/ \
  -H "Authorization: Bearer TOKEN"

# Control Device (nyalakan kipas)
curl -X POST http://localhost:8000/devices/{device_id}/control \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"component": "kipas", "state": true}'
```

### 4. Test Scenarios Checklist

| Scenario | Expected Result | Status Code |
|----------|-----------------|-------------|
| Health check | `{"status": "healthy"}` | 200 |
| Access protected endpoint tanpa token | Unauthorized | 401 |
| Access protected endpoint dengan token expired | Unauthorized | 401 |
| Claim device dengan MAC tidak terdaftar | Not Found | 404 |
| Claim device yang sudah diklaim | Bad Request | 400 |
| Claim device berhasil | Device data | 200 |
| Get devices milik user | List devices | 200 |
| Control device milik sendiri | Success message | 200 |
| Control device milik orang lain | Not Found | 404 |
| Unclaim device berhasil | Success message | 200 |

---

## 👨‍💻 Author

**Bagus** - Backend Engineer  
PKL Project 2026

---

## 📄 License

Project ini dibuat untuk keperluan pendidikan (PKL/Skripsi).