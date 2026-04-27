# Dokumentasi Integrasi Hardware ESP32 — Smart Chicken Box (PCB)

> **Versi:** 1.0.0
> **Terakhir Diperbarui:** 2026-04-27
> **Target Pembaca:** Hardware engineer / embedded developer / AI agent hardware
> **Bahasa:** Bahasa Indonesia
> **Mikrokontroler:** ESP32 (DevKit V1 atau setara)

Dokumen ini adalah **panduan lengkap** untuk mengintegrasikan mikrokontroler ESP32 dengan backend Smart Chicken Box (PCB). Semua format payload, topic MQTT, pin GPIO, dan contoh kode didokumentasikan di sini.

---

## Daftar Isi

1. [Gambaran Umum & Arsitektur](#1-gambaran-umum--arsitektur)
2. [Spesifikasi Hardware](#2-spesifikasi-hardware)
3. [Setup Awal](#3-setup-awal)
4. [Protokol MQTT](#4-protokol-mqtt)
5. [Format Payload Sensor](#5-format-payload-sensor)
6. [Format Control Command](#6-format-control-command)
7. [Kalibrasi Sensor](#7-kalibrasi-sensor)
8. [BLE Provisioning (Setup WiFi)](#8-ble-provisioning-setup-wifi)
9. [Troubleshooting](#9-troubleshooting)
10. [Contoh Kode ESP32 Lengkap](#10-contoh-kode-esp32-lengkap)
11. [Testing & Validasi](#11-testing--validasi)
12. [Rekomendasi Pengembangan Lanjutan](#12-rekomendasi-pengembangan-lanjutan)

---

## 1. Gambaran Umum & Arsitektur

### Alur Komunikasi

```
  ESP32 (Kandang Ayam)                    VPS (Docker Compose)
  ====================                    ====================

  +------------------+                    +------------------+
  | DHT22  (Suhu/RH) |--+                | MQTT Worker      |
  | MQ-135 (Amonia)  |  |   MQTT QoS 1   | (Python)         |
  | LDR    (Cahaya)  |  +--------------->| - Validasi data  |
  +------------------+  |  Publish:       | - Simpan ke DB   |
                         |  devices/      | - Cek alert      |
  +------------------+  |  {MAC}/data    | - Kirim FCM push |
  | Relay 1 (Lampu)  |  |                +--------+---------+
  | Relay 2 (Pompa)  |<-+                         |
  | Relay 3 (Kipas)  |  |   MQTT QoS 1            v
  | Relay 4 (Exhaust)|  +<---------------+------------------+
  +------------------+     Subscribe:     | PostgreSQL 15    |
                           devices/       | - sensor_logs    |
                           {MAC}/control  | - devices        |
                                          +------------------+
                                                   |
                                                   v
                                          +------------------+
                                          | FastAPI Backend   |
                                          | - REST API        |
                                          | - WebSocket       |<--- Flutter App
                                          | - MQTT Publisher   |
                                          +------------------+
```

### Alur Data Sensor (ESP32 → Database)

1. ESP32 membaca sensor (DHT22, MQ-135, LDR) setiap **30 detik**.
2. ESP32 publish JSON payload ke topic `devices/{MAC}/data` via MQTT (QoS 1).
3. MQTT Broker (Mosquitto) meneruskan pesan ke **MQTT Worker**.
4. MQTT Worker memvalidasi payload (format JSON, range sensor, MAC address).
5. Jika valid, data disimpan ke tabel `sensor_logs` di PostgreSQL.
6. `last_heartbeat` device otomatis di-update (untuk status online/offline).
7. Jika nilai sensor melewati ambang batas alert, backend kirim **FCM push notification**.

### Alur Control Command (Flutter → ESP32)

1. User menekan tombol kontrol di Flutter app (misal: "Nyalakan Lampu").
2. Flutter app mengirim `POST /api/devices/{id}/control` ke backend.
3. Backend memvalidasi akses user (role check) dan publish ke MQTT.
4. MQTT Broker meneruskan pesan ke ESP32 via topic `devices/{MAC}/control`.
5. ESP32 menerima pesan, parse JSON, dan mengaktifkan relay yang sesuai.

### Konsep Heartbeat & Status Online/Offline

- Setiap kali ESP32 publish data sensor, backend otomatis update `last_heartbeat`.
- Device dianggap **online** jika `last_heartbeat` dalam **120 detik** terakhir.
- Device dianggap **offline** jika tidak ada heartbeat lebih dari 120 detik.
- Dengan interval publish 30 detik, device akan dianggap offline setelah **4x gagal publish**.

### Lifecycle Device

```
+------------------+     +------------------+     +------------------+
| 1. REGISTER      |     | 2. CLAIM         |     | 3. AKTIF         |
| Super Admin      |---->| Admin scan QR    |---->| ESP32 publish    |
| daftarkan MAC    |     | beri nama kandang|     | data sensor      |
| via API          |     | via API/Flutter  |     | setiap 30 detik  |
+------------------+     +------------------+     +------------------+
     POST                      POST                    MQTT Publish
  /api/devices/register     /api/devices/claim      devices/{MAC}/data
```

**Step 1 — Register:** Super Admin mendaftarkan MAC address ESP32 ke sistem via API.
**Step 2 — Claim:** Admin mengklaim device (biasanya via scan QR code di Flutter app) dan memberi nama kandang.
**Step 3 — Aktif:** ESP32 mulai publish data sensor. Backend menerima dan menyimpan data.

> **PENTING:** ESP32 bisa publish data kapan saja, tapi data hanya akan disimpan jika MAC address sudah di-register DAN di-claim. Jika MAC belum dikenal, backend akan log warning `"Unknown MAC"` dan mengabaikan data.

---

## 2. Spesifikasi Hardware

### Sensor Input

| Sensor | Model | GPIO | Tipe Output | Fungsi | Library |
|--------|-------|:----:|-------------|--------|---------|
| Suhu & Kelembaban | **DHT22** (atau DHT11) | 4 | Digital | Monitoring suhu dan kelembaban kandang | `DHT sensor library` (Adafruit) |
| Gas Amonia | **MQ-135** | 34 | Analog (ADC) | Deteksi kadar gas amonia (ppm) | Tidak perlu library (analogRead) |
| Cahaya | **LDR** (Light Dependent Resistor) | 16 | Digital | Deteksi siang/malam + monitoring | Tidak perlu library (digitalRead) |

### Aktuator Output (4 Relay — Active LOW)

| Relay | Variabel | GPIO | Component Backend | Fungsi Hardware | Mode |
|:-----:|----------|:----:|-------------------|-----------------|------|
| 1 | `RELAY_LAMP` | 17 | `"lampu"` | Lampu kandang | **Otomatis** (LDR) + manual override |
| 2 | `RELAY_POMPA_MINUM` | 5 | `"pompa"` | Pompa air minum | Manual (dari Flutter/backend) |
| 3 | `RELAY_POMPA_SIRAM` | 18 | `"kipas"` | Pompa siram / kipas | Manual (dari Flutter/backend) |
| 4 | `RELAY_EXHAUST` | 19 | `"exhaust_fan"` | Kipas exhaust (buang amonia) | Manual (dari Flutter/backend) |

> **Catatan Active LOW:** Relay module yang umum digunakan adalah **active LOW**. Artinya:
> - `digitalWrite(pin, LOW)` = Relay **NYALA** (ON)
> - `digitalWrite(pin, HIGH)` = Relay **MATI** (OFF)
> - Saat boot, semua relay di-set `HIGH` (mati) untuk mencegah aktuator menyala tidak terkendali.

### Komponen Pendukung

| Komponen | GPIO | Fungsi |
|----------|:----:|--------|
| LED Status (built-in) | 2 | Indikator koneksi WiFi. ON = terhubung, OFF = mode BLE. |
| Tombol Reset | 0 (Pull-up) | Factory reset. Tahan 3 detik untuk menghapus konfigurasi WiFi dan restart. |

### Diagram Pin GPIO

```
ESP32 DevKit V1
================

        +--[USB]--+
   3V3  |         | VIN
   GND  |         | GND
   D15  |         | D13
    D2  | (LED)   | D12
    D4  | (DHT22) | D14
   D16  | (LDR)   | D27
   D17  | (RELAY1)| D26
    D5  | (RELAY2)| D25
   D18  | (RELAY3)| D33
   D19  | (RELAY4)| D32
   D21  |         | D35
    RX  |         | D34  (MQ-135)
    TX  |         | VN
        +---------+

Pin yang digunakan:
  GPIO  0 = Tombol Reset (INPUT_PULLUP)
  GPIO  2 = LED Status (OUTPUT)
  GPIO  4 = DHT22 Data (INPUT)
  GPIO 16 = LDR Sensor (INPUT)
  GPIO 17 = Relay 1 - Lampu (OUTPUT, Active LOW)
  GPIO  5 = Relay 2 - Pompa Minum (OUTPUT, Active LOW)
  GPIO 18 = Relay 3 - Pompa Siram (OUTPUT, Active LOW)
  GPIO 19 = Relay 4 - Exhaust Fan (OUTPUT, Active LOW)
  GPIO 34 = MQ-135 Analog (INPUT, ADC1_CH6)
```

> **PENTING GPIO 34:** Pin ini adalah **input-only** pada ESP32. Tidak bisa digunakan sebagai output. Cocok untuk sensor analog (ADC).

### Library Dependencies

| Library | Versi | Sumber | Fungsi |
|---------|-------|--------|--------|
| `DHT sensor library` | 1.4.6+ | Adafruit (Arduino Library Manager) | Baca sensor DHT22/DHT11 |
| `PubSubClient` | 2.8+ | Nick O'Leary (Arduino Library Manager) | MQTT client |
| `ArduinoJson` | 7.x | Benoit Blanchon (Arduino Library Manager) | Parse & serialize JSON |
| `WiFi.h` | — | Built-in ESP32 | Koneksi WiFi |
| `BLEDevice.h` | — | Built-in ESP32 | BLE provisioning |
| `Preferences.h` | — | Built-in ESP32 | Simpan konfigurasi WiFi ke NVS (Non-Volatile Storage) |

---

## 3. Setup Awal

### 3.1 Install Arduino IDE & Board ESP32

1. Download dan install [Arduino IDE](https://www.arduino.cc/en/software) versi 2.x.
2. Buka **File → Preferences → Additional Board Manager URLs**, tambahkan:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Buka **Tools → Board → Board Manager**, cari `esp32`, install **"ESP32 by Espressif Systems"**.
4. Pilih board: **Tools → Board → ESP32 Dev Module**.

### 3.2 Install Library

Buka **Tools → Manage Libraries**, install:

1. `DHT sensor library` by Adafruit
2. `Adafruit Unified Sensor` by Adafruit (dependency DHT)
3. `PubSubClient` by Nick O'Leary
4. `ArduinoJson` by Benoit Blanchon

### 3.3 Konfigurasi MQTT Broker

ESP32 perlu tahu alamat MQTT broker. Konfigurasi ini di-hardcode di kode:

```cpp
const char* MQTT_BROKER = "43.153.201.137";  // IP publik VPS
const int   MQTT_PORT   = 1883;
const char* MQTT_USER   = "device_user";
const char* MQTT_PASS   = "pkl_pcb_iot_bagus_2026";
```

> **Development:** Jika broker di jaringan lokal, gunakan IP lokal (misal `192.168.1.100`).
> **Production:** Gunakan IP publik VPS atau domain.

### 3.4 Konfigurasi WiFi

WiFi **TIDAK** di-hardcode. Konfigurasi dilakukan via **BLE Provisioning** dari Flutter app:

1. Upload kode ke ESP32.
2. ESP32 boot → cek apakah ada konfigurasi WiFi tersimpan di NVS.
3. Jika **tidak ada** → masuk mode BLE (LED mati, BLE advertising aktif).
4. Buka Flutter app → scan BLE → pilih device → kirim SSID & password.
5. ESP32 simpan ke NVS → restart → connect WiFi.

Lihat [Bagian 8: BLE Provisioning](#8-ble-provisioning-setup-wifi) untuk detail lengkap.

### 3.5 Mendapatkan MAC Address ESP32

MAC address dibutuhkan untuk mendaftarkan device ke backend. Cara mendapatkannya:

**Cara 1 — Dari Serial Monitor:**
Upload sketch kosong dengan kode berikut, buka Serial Monitor (115200 baud):
```cpp
void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  Serial.println("MAC Address: " + WiFi.macAddress());
}
void loop() {}
```

**Cara 2 — Dari BLE Device Name:**
Saat ESP32 dalam mode BLE, nama device yang muncul adalah `Kandang Ayam AABBCCDDEEFF` (MAC tanpa colon).

**Cara 3 — Dari Serial Monitor saat boot:**
Kode utama akan print topic MQTT saat boot, yang mengandung MAC address:
```
--- TOPICS SET ---
Publish : devices/AABBCCDDEEFF/data
Control : devices/AABBCCDDEEFF/control
```

### 3.6 Mendaftarkan Device ke Backend

Setelah mendapatkan MAC address, Admin harus mendaftarkan device ke backend:

**Step 1 — Register MAC (Super Admin):**
```bash
curl -X POST "{{BASE_URL}}/api/devices/register" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF"}'
```

**Step 2 — Claim Device (Admin):**
```bash
curl -X POST "{{BASE_URL}}/api/devices/claim" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF", "name": "Kandang Utara"}'
```

> **Format MAC:** Backend menerima dua format:
> - Dengan colon: `AA:BB:CC:DD:EE:FF`
> - Tanpa colon: `AABBCCDDEEFF`
> Backend akan otomatis normalize ke format uppercase dengan colon.

---

## 4. Protokol MQTT

### 4.1 Koneksi ke Broker

| Parameter | Nilai | Keterangan |
|-----------|-------|------------|
| **Broker** | `43.153.201.137` (atau domain Anda) | IP publik VPS yang menjalankan Mosquitto |
| **Port** | `1883` | Port default MQTT (tanpa TLS) |
| **Username** | `device_user` | Kredensial autentikasi broker |
| **Password** | `pkl_pcb_iot_bagus_2026` | Kredensial autentikasi broker |
| **Client ID** | `ESP32-{MAC_TANPA_COLON}` | Unik per device, contoh: `ESP32-AABBCCDDEEFF` |
| **Keep Alive** | 60 detik | Interval ping ke broker agar koneksi tidak timeout |
| **QoS** | 1 (at least once) | Pesan dijamin terkirim minimal 1 kali |

### 4.2 Struktur Topic

ESP32 menggunakan **2 topic** — satu untuk publish data sensor, satu untuk subscribe perintah kontrol:

```
devices/{MAC_ADDRESS}/data       ← ESP32 PUBLISH ke sini (sensor data)
devices/{MAC_ADDRESS}/control    ← ESP32 SUBSCRIBE di sini (control command)
```

**Format MAC Address di Topic:**

| Format | Contoh | Diterima Backend? |
|--------|--------|:-----------------:|
| Tanpa colon (uppercase) | `devices/AABBCCDDEEFF/data` | **Ya** (direkomendasikan) |
| Dengan colon (uppercase) | `devices/AA:BB:CC:DD:EE:FF/data` | **Ya** (auto-normalize) |
| Lowercase | `devices/aabbccddeeff/data` | **Ya** (auto-normalize) |

> **Rekomendasi:** Gunakan format **tanpa colon, uppercase** untuk konsistensi.

### 4.3 Cara Mendapatkan MAC untuk Topic

```cpp
String getDeviceID() {
  String mac = WiFi.macAddress();  // Format: "AA:BB:CC:DD:EE:FF"
  mac.replace(":", "");            // Jadi: "AABBCCDDEEFF"
  return mac;
}

// Hasil:
// TOPIC_DATA    = "devices/AABBCCDDEEFF/data"
// TOPIC_CONTROL = "devices/AABBCCDDEEFF/control"
```

### 4.4 Reconnection Strategy

Jika koneksi MQTT terputus, ESP32 harus reconnect otomatis:

```
1. Cek apakah client.connected() == false
2. Jika tidak connected, panggil client.connect(...)
3. Jika connect gagal, tunggu 2 detik, coba lagi
4. Setelah berhasil connect, subscribe ulang ke topic control
5. Lanjutkan publish data sensor seperti biasa
```

> **PENTING:** Setelah reconnect, ESP32 **HARUS** subscribe ulang ke topic control. Subscription tidak bertahan setelah disconnect.

---

## 5. Format Payload Sensor

### 5.1 JSON Schema

ESP32 publish payload JSON berikut ke topic `devices/{MAC}/data` setiap **30 detik**:

```json
{
  "temperature": 30.5,
  "humidity": 75.0,
  "ammonia": 12.5,
  "light_level": 1
}
```

### 5.2 Spesifikasi Field

| Field | Tipe | Wajib | Min | Max | Satuan | Sumber Sensor |
|-------|------|:-----:|----:|----:|--------|---------------|
| `temperature` | float | **Ya** | -40 | 80 | Celsius (C) | DHT22 / DHT11 |
| `humidity` | float | **Ya** | 0 | 100 | Persen (%) | DHT22 / DHT11 |
| `ammonia` | float | **Ya** | 0 | 500 | Parts per million (ppm) | MQ-135 (ADC) |
| `light_level` | integer | **Ya** | 0 | 1 | Binary | LDR (digital) |

**Keterangan `light_level`:**
- `0` = Gelap (malam / cahaya rendah)
- `1` = Terang (siang / cahaya cukup)

### 5.3 Validasi Backend

Backend memvalidasi setiap payload yang masuk. Jika tidak valid, data **dibuang** (tidak disimpan ke database):

| Validasi | Kondisi Gagal | Log Backend |
|----------|---------------|-------------|
| Format JSON | Payload bukan JSON valid | `"Payload bukan JSON valid"` |
| Encoding | Payload bukan UTF-8 | `"Payload bukan UTF-8 valid"` |
| Field wajib | Salah satu field hilang | `"Payload tidak lengkap: field 'xxx' tidak ditemukan"` |
| Tipe data | Field bukan angka (misal string) | `"Data sensor tidak valid"` |
| Range suhu | temperature < -40 atau > 80 | `"Data sensor tidak valid"` |
| Range humidity | humidity < 0 atau > 100 | `"Data sensor tidak valid"` |
| Range ammonia | ammonia < 0 atau > 500 | `"Data sensor tidak valid"` |
| MAC address | MAC tidak terdaftar di database | `"Unknown MAC: AABBCCDDEEFF"` |
| Topic format | Topic bukan `devices/{mac}/data` | `"Format topic tidak valid"` |

### 5.4 Contoh Payload Valid

```json
{"temperature": 28.5, "humidity": 72.0, "ammonia": 8.3, "light_level": 1}
```

### 5.5 Contoh Payload TIDAK Valid

```json
// Field hilang (ammonia tidak ada)
{"temperature": 28.5, "humidity": 72.0, "light_level": 1}

// Suhu di luar range
{"temperature": 150.0, "humidity": 72.0, "ammonia": 8.3, "light_level": 1}

// Tipe data salah (string bukan float)
{"temperature": "panas", "humidity": 72.0, "ammonia": 8.3, "light_level": 1}

// Bukan JSON
suhu=28.5&humidity=72.0
```

### 5.6 Penanganan Sensor Error di ESP32

Jika sensor gagal dibaca (misal DHT22 return `NaN`), kirim nilai **0** agar payload tetap valid:

```cpp
float suhu = dht.readTemperature();
float hum  = dht.readHumidity();

doc["temperature"] = isnan(suhu) ? 0.0 : suhu;
doc["humidity"]    = isnan(hum)  ? 0.0 : hum;
doc["ammonia"]     = isnan(ammonia) ? 0.0 : ammonia;
doc["light_level"] = digitalRead(LDR_PIN);
```

> **Catatan:** Nilai 0 masih dalam range valid (-40 sampai 80 untuk suhu), jadi backend akan menerimanya. Namun, ini bisa menyebabkan **false alert** jika threshold minimum suhu > 0. Pertimbangkan untuk menambahkan flag `"sensor_error": true` di payload jika ingin membedakan data real vs error (memerlukan perubahan backend).

### 5.7 Interval Publish

| Parameter | Nilai | Keterangan |
|-----------|-------|------------|
| **Interval** | 30 detik | Sweet spot antara responsivitas dan efisiensi |
| **Heartbeat timeout** | 120 detik | Backend anggap device offline jika tidak ada data 120 detik |
| **Toleransi** | 4x gagal publish | Dengan interval 30 detik, device offline setelah 2 menit tanpa data |

### 5.8 Alert Thresholds

Backend otomatis mendeteksi kondisi berbahaya berdasarkan threshold berikut:

| Kondisi | Threshold | Alert Message |
|---------|-----------|---------------|
| Suhu terlalu panas | temperature > **35.0** C | `"Suhu Terlalu Panas!"` |
| Suhu terlalu dingin | temperature < **20.0** C | `"Suhu Terlalu Dingin!"` |
| Amonia berbahaya | ammonia > **20.0** ppm | `"Kadar Amonia Berbahaya!"` |

**Perilaku alert:**
- Backend kirim **FCM push notification** ke admin/operator device.
- **Cooldown:** Maksimal 1 notifikasi per device per **5 menit** (anti-spam).
- Threshold bisa diubah via environment variable di backend (`.env`).

> **PENTING untuk hardware engineer:** ESP32 **TIDAK PERLU** mendeteksi alert sendiri. Cukup kirim data sensor apa adanya. Semua logika alert ditangani oleh backend.

---

## 6. Format Control Command

### 6.1 JSON Schema

ESP32 menerima perintah kontrol dari backend via topic `devices/{MAC}/control`:

```json
{
  "component": "lampu",
  "state": "ON"
}
```

### 6.2 Spesifikasi Field

| Field | Tipe | Nilai Valid | Keterangan |
|-------|------|------------|------------|
| `component` | string | `"lampu"`, `"pompa"`, `"kipas"`, `"exhaust_fan"`, `"pakan_otomatis"` | Komponen yang dikontrol |
| `state` | string atau boolean | `"ON"`, `"OFF"`, `true`, `false` | Status yang diinginkan |

> **Catatan `state`:** Backend mengirim `"ON"` / `"OFF"` (string). Namun, Flutter app mungkin mengirim `true` / `false` (boolean). Kode ESP32 harus handle **kedua format**.

### 6.3 Mapping Component ke Relay

| Component | Relay | GPIO | Fungsi Hardware | Aksi ON | Aksi OFF |
|-----------|:-----:|:----:|-----------------|---------|----------|
| `"lampu"` | 1 | 17 | Lampu kandang | `digitalWrite(17, LOW)` | `digitalWrite(17, HIGH)` |
| `"pompa"` | 2 | 5 | Pompa air minum | `digitalWrite(5, LOW)` | `digitalWrite(5, HIGH)` |
| `"kipas"` | 3 | 18 | Pompa siram / kipas | `digitalWrite(18, LOW)` | `digitalWrite(18, HIGH)` |
| `"exhaust_fan"` | 4 | 19 | Kipas exhaust | `digitalWrite(19, LOW)` | `digitalWrite(19, HIGH)` |
| `"pakan_otomatis"` | — | — | (Tidak ada hardware) | **Diabaikan** | **Diabaikan** |

> **Catatan `pakan_otomatis`:** Component ini masih ada di schema backend untuk backward compatibility, tapi ESP32 **mengabaikan** perintah ini karena tidak ada hardware servo/load cell.

### 6.4 Mode Lampu: Otomatis vs Manual

Relay lampu memiliki **2 mode operasi**:

**Mode Otomatis (default saat boot):**
- LDR membaca kondisi cahaya setiap 2 detik.
- Jika gelap (`LDR == HIGH`) → lampu nyala (`RELAY_LAMP = LOW`).
- Jika terang (`LDR == LOW`) → lampu mati (`RELAY_LAMP = HIGH`).

**Mode Manual (setelah terima control command):**
- Saat ESP32 menerima control command `"lampu"`, mode otomatis **dinonaktifkan**.
- Lampu dikontrol sepenuhnya oleh perintah dari Flutter/backend.
- Mode otomatis **tidak kembali** sampai ESP32 di-restart.

```
Boot ESP32
    |
    v
[Mode Otomatis]  ←── LDR kontrol lampu
    |
    | (Terima control command "lampu")
    v
[Mode Manual]    ←── Flutter/backend kontrol lampu
    |
    | (Restart ESP32)
    v
[Mode Otomatis]  ←── Kembali ke otomatis
```

**Implementasi di kode:**

```cpp
bool modeLampuOtomatis = true;  // Default: otomatis

void handleControl(String component, bool turnOn) {
  if (component == "lampu") {
    modeLampuOtomatis = false;  // Disable otomatis
    digitalWrite(RELAY_LAMP, turnOn ? LOW : HIGH);
  }
  // ... relay lain ...
}

void loop() {
  // Otomatis lampu hanya jalan jika mode otomatis aktif
  if (modeLampuOtomatis) {
    digitalWrite(RELAY_LAMP, digitalRead(LDR_PIN) == HIGH ? LOW : HIGH);
  }
}
```

### 6.5 Contoh Implementasi Callback MQTT

```cpp
void callback(char* topic, byte* payload, unsigned int length) {
  // Hanya proses topic control
  if (String(topic) != TOPIC_CONTROL) return;

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.println("Gagal parsing JSON Control");
    return;
  }

  String component = doc["component"];

  // Handle state: bisa string "ON"/"OFF" atau boolean true/false
  bool turnOn = false;
  if (doc["state"].is<bool>()) {
    turnOn = doc["state"].as<bool>();
  } else {
    String state = doc["state"];
    turnOn = (state == "ON" || state == "true");
  }

  // Mapping component ke relay
  if (component == "lampu") {
    modeLampuOtomatis = false;
    digitalWrite(RELAY_LAMP, turnOn ? LOW : HIGH);
  }
  else if (component == "pompa") {
    digitalWrite(RELAY_POMPA_MINUM, turnOn ? LOW : HIGH);
  }
  else if (component == "kipas") {
    digitalWrite(RELAY_POMPA_SIRAM, turnOn ? LOW : HIGH);
  }
  else if (component == "exhaust_fan") {
    digitalWrite(RELAY_EXHAUST, turnOn ? LOW : HIGH);
  }
  // "pakan_otomatis" diabaikan (tidak ada hardware)

  Serial.printf("Kontrol: %s = %s\n", component.c_str(), turnOn ? "ON" : "OFF");
}
```

---

## 7. Kalibrasi Sensor

### 7.1 DHT22 vs DHT11 — Cara Switch

Kode mendukung **kedua sensor** dengan mengubah satu baris:

```cpp
// ===== PILIH SALAH SATU =====
#define DHT_TYPE DHT22    // Akurasi tinggi: +/- 0.5C, range -40 s/d 80C
// #define DHT_TYPE DHT11 // Akurasi rendah: +/- 2C, range 0 s/d 50C
// =============================

#define DHT_PIN 4
DHT dht(DHT_PIN, DHT_TYPE);
```

**Perbandingan:**

| Spesifikasi | DHT22 | DHT11 |
|-------------|-------|-------|
| Range suhu | -40 s/d 80 C | 0 s/d 50 C |
| Akurasi suhu | +/- 0.5 C | +/- 2 C |
| Range humidity | 0 s/d 100% | 20 s/d 80% |
| Akurasi humidity | +/- 2% | +/- 5% |
| Interval baca minimum | 2 detik | 1 detik |
| Harga | Lebih mahal | Lebih murah |

> **Rekomendasi:** Gunakan **DHT22** untuk monitoring kandang ayam karena akurasi lebih tinggi dan range suhu lebih luas. DHT11 bisa digunakan sebagai alternatif murah jika akurasi tidak kritis.

### 7.2 MQ-135 — Kalibrasi R0

Sensor MQ-135 memerlukan kalibrasi **R0** (resistansi sensor di udara bersih) untuk pembacaan yang akurat.

**Langkah Kalibrasi:**

1. **Letakkan sensor di udara bersih** (outdoor, jauh dari sumber gas).
2. **Nyalakan sensor selama 24-48 jam** (burn-in / preheat).
3. **Baca nilai ADC** dan hitung R0:

```cpp
// Kode kalibrasi R0 (jalankan sekali di udara bersih)
void calibrateMQ135() {
  Serial.println("Kalibrasi MQ-135 dimulai...");
  Serial.println("Pastikan sensor di udara bersih!");

  float total = 0;
  int samples = 50;

  for (int i = 0; i < samples; i++) {
    int adc = analogRead(MQ135_PIN);
    float voltage = adc * (3.3 / 4095.0);
    float rs = 10.0 * ((3.3 - voltage) / voltage);  // Rs = RL * (Vc - Vout) / Vout
    total += rs;
    delay(100);
  }

  float rs_avg = total / samples;
  float r0 = rs_avg / 3.6;  // Rasio Rs/R0 di udara bersih untuk MQ-135 = ~3.6

  Serial.printf("R0 = %.2f\n", r0);
  Serial.println("Masukkan nilai ini ke variabel R0 di kode utama.");
}
```

4. **Masukkan nilai R0** ke variabel di kode utama:

```cpp
float R0 = 5.27;  // Ganti dengan hasil kalibrasi Anda
```

**Formula Konversi ADC ke PPM Ammonia:**

```cpp
int mq_adc = analogRead(MQ135_PIN);
float voltage = mq_adc * (3.3 / 4095.0);
float ammonia = 0;

if (voltage > 0.1 && R0 > 0) {
  float rs = 10.0 * ((3.3 - voltage) / voltage);
  ammonia = 102.2 * pow(rs / R0, -2.473);

  // Clamp ke range valid
  if (ammonia > 500.0) ammonia = 500.0;
  if (ammonia < 0.0) ammonia = 0.0;
}
```

> **PENTING:** Nilai R0 berbeda untuk setiap unit sensor MQ-135. Kalibrasi **WAJIB** dilakukan per sensor. Nilai default `R0 = 5.27` hanya contoh.

### 7.3 LDR — Threshold Cahaya

LDR dibaca secara **digital** (bukan analog):

```cpp
int cahaya = digitalRead(LDR_PIN);
// HIGH = gelap (resistansi LDR tinggi, voltage drop)
// LOW  = terang (resistansi LDR rendah)
```

> **Catatan:** Threshold HIGH/LOW tergantung pada **resistor pembagi tegangan** yang digunakan di rangkaian LDR. Jika terlalu sensitif atau kurang sensitif, sesuaikan nilai resistor.

**Rangkaian LDR (Voltage Divider):**

```
3.3V ──── LDR ──┬── Resistor (10K) ──── GND
                 |
                 └── GPIO 16 (INPUT)
```

- Gelap → LDR resistansi tinggi → voltage di GPIO naik → `HIGH`
- Terang → LDR resistansi rendah → voltage di GPIO turun → `LOW`

---

## 8. BLE Provisioning (Setup WiFi)

### 8.1 Cara Kerja

ESP32 menggunakan **Bluetooth Low Energy (BLE)** untuk menerima konfigurasi WiFi dari Flutter app. Ini menghilangkan kebutuhan untuk hardcode SSID/password di kode.

```
+------------------+                    +------------------+
| Flutter App      |   BLE Connection   | ESP32            |
|                  |<------------------>|                  |
| 1. Scan BLE      |                    | BLE Server aktif |
| 2. Connect       |                    | (mode BLE)       |
| 3. Kirim JSON:   |------------------->|                  |
|    {ssid, pass}  |                    | 4. Simpan ke NVS |
|                  |                    | 5. Restart       |
|                  |                    | 6. Connect WiFi  |
+------------------+                    +------------------+
```

### 8.2 Kapan Mode BLE Aktif?

Mode BLE **hanya aktif** jika ESP32 **gagal connect WiFi** saat boot:

```
Boot ESP32
    |
    v
Cek NVS: ada konfigurasi WiFi?
    |
    +-- Ya --> Coba connect WiFi (timeout 10 detik)
    |              |
    |              +-- Berhasil --> Mode WiFi + MQTT (normal)
    |              |
    |              +-- Gagal --> Mode BLE (fallback)
    |
    +-- Tidak --> Mode BLE (pertama kali)
```

**Indikator LED:**
- LED **menyala** = WiFi terhubung (mode normal)
- LED **mati** = Mode BLE aktif (menunggu konfigurasi)

### 8.3 BLE Service & Characteristic

| Parameter | Nilai |
|-----------|-------|
| **Device Name** | `Kandang Ayam {MAC_TANPA_COLON}` (contoh: `Kandang Ayam AABBCCDDEEFF`) |
| **Service UUID** | `4fafc201-1fb5-459e-8fcc-c5c9c331914b` |
| **Characteristic UUID** | `beb5483e-36e1-4688-b7f5-ea07361b26a8` |
| **Characteristic Property** | WRITE + WRITE_NR |

### 8.4 Format Data BLE (Flutter → ESP32)

Flutter app mengirim JSON berikut ke BLE characteristic:

```json
{
  "ssid": "Nama_WiFi",
  "pass": "Password_WiFi"
}
```

| Field | Tipe | Keterangan |
|-------|------|------------|
| `ssid` | string | Nama jaringan WiFi |
| `pass` | string | Password WiFi |

### 8.5 Alur di Sisi ESP32

1. ESP32 menerima data BLE (JSON).
2. Parse JSON, ambil `ssid` dan `pass`.
3. Simpan ke **NVS** (Non-Volatile Storage) menggunakan library `Preferences`:
   ```cpp
   preferences.begin("wifi-conf", false);
   preferences.putString("ssid", ssid);
   preferences.putString("pass", pass);
   preferences.end();
   ```
4. Restart ESP32 (`ESP.restart()`).
5. Setelah restart, ESP32 baca NVS → connect WiFi → mode normal.

### 8.6 Factory Reset

Jika WiFi berubah atau konfigurasi salah, user bisa melakukan **factory reset**:

1. **Tahan tombol GPIO 0** selama **3 detik**.
2. ESP32 akan menghapus konfigurasi WiFi dari NVS.
3. ESP32 restart otomatis.
4. Setelah restart, ESP32 masuk mode BLE (karena tidak ada konfigurasi WiFi).
5. User bisa kirim konfigurasi WiFi baru via Flutter app.

```cpp
// Implementasi factory reset (di dalam loop)
if (digitalRead(RESET_BTN) == LOW) {
  long start = millis();
  while (digitalRead(RESET_BTN) == LOW) {
    if (millis() - start > 3000) {
      Serial.println("RESET PABRIK!");
      preferences.begin("wifi-conf", false);
      preferences.clear();
      preferences.end();
      ESP.restart();
    }
  }
}
```

---

## 9. Troubleshooting

### 9.1 Tabel Masalah Umum

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| Backend log: `"Unknown MAC: AABBCCDDEEFF"` | MAC address belum di-register atau belum di-claim di backend | 1. Register MAC via API: `POST /api/devices/register`<br>2. Claim device via API: `POST /api/devices/claim` |
| Backend log: `"Payload tidak lengkap: field 'xxx' tidak ditemukan"` | Salah satu field wajib (`temperature`, `humidity`, `ammonia`, `light_level`) tidak ada di JSON | Pastikan payload JSON punya **4 field wajib**. Cek kode `serializeJson()`. |
| Backend log: `"Data sensor tidak valid"` | Nilai sensor di luar range yang diizinkan | 1. Cek pembacaan sensor (mungkin rusak atau kabel lepas)<br>2. Cek range: suhu -40~80, humidity 0~100, ammonia 0~500 |
| Backend log: `"Payload bukan JSON valid"` | ESP32 mengirim data yang bukan format JSON | Cek kode `serializeJson()`. Pastikan buffer cukup besar (256 byte). |
| Backend log: `"Format topic tidak valid"` | Topic MQTT tidak sesuai format `devices/{mac}/data` | Cek variabel `TOPIC_DATA`. Pastikan format: `devices/AABBCCDDEEFF/data` |
| Device status **"offline"** di dashboard | Tidak ada heartbeat dalam 120 detik | 1. Cek koneksi WiFi ESP32 (LED menyala?)<br>2. Cek koneksi MQTT (`client.connected()`?)<br>3. Pastikan publish berjalan setiap 30 detik |
| Control command tidak diterima ESP32 | ESP32 tidak subscribe ke topic control | 1. Pastikan `client.subscribe(TOPIC_CONTROL)` dipanggil setelah connect<br>2. Pastikan subscribe ulang setelah reconnect |
| MQTT connect gagal (`rc=-2` atau `rc=5`) | Broker unreachable atau credentials salah | 1. Ping broker dari jaringan ESP32<br>2. Cek `MQTT_BROKER`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASS`<br>3. Cek firewall VPS (port 1883 harus terbuka) |
| WiFi connect gagal (timeout) | SSID/password salah atau signal lemah | 1. Factory reset (tahan tombol 3 detik)<br>2. Kirim ulang konfigurasi WiFi via BLE<br>3. Pastikan ESP32 dalam jangkauan WiFi |
| BLE tidak muncul di scan Flutter | ESP32 sudah terhubung WiFi (BLE hanya aktif jika WiFi gagal) | 1. Factory reset untuk masuk mode BLE<br>2. Atau matikan WiFi router agar ESP32 gagal connect |
| Relay tidak merespons control command | Wiring salah atau relay module rusak | 1. Test relay manual: `digitalWrite(pin, LOW)` di Serial Monitor<br>2. Cek wiring: VCC, GND, IN<br>3. Cek apakah relay active LOW atau HIGH |
| Pembacaan MQ-135 selalu 0 ppm | Sensor belum preheat atau R0 belum dikalibrasi | 1. Nyalakan sensor 24-48 jam (burn-in)<br>2. Kalibrasi R0 di udara bersih (lihat Bagian 7.2) |
| Pembacaan DHT22 return `NaN` | Kabel data lepas atau sensor rusak | 1. Cek wiring: VCC (3.3V), GND, DATA (GPIO 4)<br>2. Tambahkan resistor pull-up 10K antara VCC dan DATA<br>3. Ganti sensor jika tetap NaN |
| ESP32 restart terus-menerus (boot loop) | Power supply tidak cukup atau kode crash | 1. Gunakan power supply 5V 2A (bukan USB laptop)<br>2. Cek Serial Monitor untuk error message<br>3. Cek apakah ada `delay()` terlalu lama di callback |

### 9.2 Cara Membaca Log Backend

Log backend bisa dilihat via Docker:

```bash
# Lihat log MQTT Worker (real-time)
docker compose logs -f mqtt_worker

# Lihat log Backend (real-time)
docker compose logs -f backend

# Filter log untuk MAC address tertentu
docker compose logs mqtt_worker | grep "AABBCCDDEEFF"
```

**Contoh log normal (data diterima):**
```
INFO  - Data masuk & Heartbeat updated: Kandang Utara
```

**Contoh log error (MAC tidak dikenal):**
```
WARNING - Unknown MAC: AABBCCDDEEFF (raw: AABBCCDDEEFF)
```

**Contoh log alert (threshold terlampaui):**
```
WARNING - ALERT untuk Kandang Utara: Suhu Terlalu Panas! Kadar Amonia Berbahaya!
```

---

## 10. Contoh Kode ESP32 Lengkap

Kode di bawah ini adalah **implementasi lengkap** yang siap di-upload ke ESP32. Mendukung switch antara DHT22 dan DHT11 dengan mengubah satu baris `#define`.

```cpp
// ================================================================
// Smart Chicken Box (PCB) — Firmware ESP32
// ================================================================
// Versi  : 2.0.0 (Refactored)
// Sensor : DHT22/DHT11, MQ-135, LDR
// Output : 4x Relay (Active LOW)
// Koneksi: WiFi + MQTT (BLE provisioning untuk setup WiFi)
// ================================================================

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <WiFi.h>
#include <Preferences.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <DHT.h>

// ================================================================
// 1. KONFIGURASI PIN GPIO
// ================================================================
#define RESET_BTN          0    // Tombol factory reset (tahan 3 detik)
#define LED_PIN            2    // LED status (built-in)
#define DHT_PIN            4    // Sensor suhu & humidity
#define LDR_PIN            16   // Sensor cahaya (digital)
#define RELAY_LAMP         17   // Relay 1 — Lampu kandang
#define RELAY_POMPA_MINUM  5    // Relay 2 — Pompa air minum
#define RELAY_POMPA_SIRAM  18   // Relay 3 — Pompa siram / kipas
#define RELAY_EXHAUST      19   // Relay 4 — Kipas exhaust
#define MQ135_PIN          34   // Sensor amonia (ADC, input-only)

// ================================================================
// 2. KONFIGURASI SENSOR
// ================================================================
// ===== PILIH SENSOR SUHU (uncomment salah satu) =====
#define DHT_TYPE DHT22       // Akurasi tinggi: +/- 0.5C, range -40 s/d 80C
// #define DHT_TYPE DHT11    // Akurasi rendah: +/- 2C, range 0 s/d 50C
// =====================================================

DHT dht(DHT_PIN, DHT_TYPE);

// Kalibrasi MQ-135 (jalankan kalibrasi di udara bersih, lihat dokumentasi)
float R0 = 5.27;

// ================================================================
// 3. KONFIGURASI MQTT
// ================================================================
const char* MQTT_BROKER = "43.153.201.137";  // IP publik VPS
const int   MQTT_PORT   = 1883;
const char* MQTT_USER   = "device_user";
const char* MQTT_PASS   = "pkl_pcb_iot_bagus_2026";

// ================================================================
// 4. KONFIGURASI BLE
// ================================================================
#define DEVICE_NAME_PREFIX  "Kandang Ayam "
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// ================================================================
// 5. KONFIGURASI TIMING
// ================================================================
const long INTERVAL_BACA_LDR     = 2000;   // Cek LDR setiap 2 detik
const long INTERVAL_KIRIM_SENSOR = 30000;  // Publish sensor setiap 30 detik

// ================================================================
// 6. VARIABEL GLOBAL
// ================================================================
String TOPIC_DATA;
String TOPIC_CONTROL;

Preferences preferences;
WiFiClient espClient;
PubSubClient client(espClient);

bool deviceConnected = false;
bool wifiConnected = false;
bool modeLampuOtomatis = true;

unsigned long lastLdrCheck = 0;
unsigned long lastSensorPublish = 0;

// ================================================================
// 7. FUNGSI BANTUAN
// ================================================================

// Mendapatkan MAC address tanpa colon (untuk topic MQTT)
String getDeviceID() {
  String mac = WiFi.macAddress();
  mac.replace(":", "");
  return mac;
}

// Setup topic MQTT berdasarkan MAC address
void setupTopics() {
  String id = getDeviceID();
  TOPIC_DATA    = "devices/" + id + "/data";
  TOPIC_CONTROL = "devices/" + id + "/control";
  Serial.println("Topic Publish : " + TOPIC_DATA);
  Serial.println("Topic Control : " + TOPIC_CONTROL);
}

// ================================================================
// 8. BACA SENSOR
// ================================================================

// Baca semua sensor dan return sebagai JSON string
String bacaSensor() {
  // --- DHT22 / DHT11 ---
  float suhu = dht.readTemperature();
  float hum  = dht.readHumidity();

  // --- MQ-135 (Amonia) ---
  int mq_adc = analogRead(MQ135_PIN);
  float voltage = mq_adc * (3.3 / 4095.0);
  float ammonia = 0;
  if (voltage > 0.1 && R0 > 0) {
    float rs = 10.0 * ((3.3 - voltage) / voltage);
    ammonia = 102.2 * pow(rs / R0, -2.473);
    if (ammonia > 500.0) ammonia = 500.0;
    if (ammonia < 0.0) ammonia = 0.0;
  }

  // --- LDR (Cahaya) ---
  int lightLevel = digitalRead(LDR_PIN) == HIGH ? 0 : 1;
  // HIGH = gelap (0), LOW = terang (1)

  // --- Buat JSON ---
  StaticJsonDocument<256> doc;
  doc["temperature"] = isnan(suhu) ? 0.0 : suhu;
  doc["humidity"]    = isnan(hum)  ? 0.0 : hum;
  doc["ammonia"]     = isnan(ammonia) ? 0.0 : ammonia;
  doc["light_level"] = lightLevel;

  char buffer[256];
  serializeJson(doc, buffer);
  return String(buffer);
}

// ================================================================
// 9. HANDLE CONTROL COMMAND (MQTT CALLBACK)
// ================================================================

void callback(char* topic, byte* payload, unsigned int length) {
  if (String(topic) != TOPIC_CONTROL) return;

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.println("Gagal parsing JSON Control");
    return;
  }

  String component = doc["component"];

  // Handle state: string "ON"/"OFF" atau boolean true/false
  bool turnOn = false;
  if (doc["state"].is<bool>()) {
    turnOn = doc["state"].as<bool>();
  } else {
    String state = doc["state"];
    turnOn = (state == "ON" || state == "true");
  }

  // Mapping component ke relay (Active LOW)
  if (component == "lampu") {
    modeLampuOtomatis = false;  // Disable mode otomatis
    digitalWrite(RELAY_LAMP, turnOn ? LOW : HIGH);
  }
  else if (component == "pompa") {
    digitalWrite(RELAY_POMPA_MINUM, turnOn ? LOW : HIGH);
  }
  else if (component == "kipas") {
    digitalWrite(RELAY_POMPA_SIRAM, turnOn ? LOW : HIGH);
  }
  else if (component == "exhaust_fan") {
    digitalWrite(RELAY_EXHAUST, turnOn ? LOW : HIGH);
  }
  // "pakan_otomatis" diabaikan (tidak ada hardware)

  Serial.printf("Kontrol: %s = %s\n", component.c_str(), turnOn ? "ON" : "OFF");
}

// ================================================================
// 10. MQTT RECONNECT
// ================================================================

void reconnectMQTT() {
  if (!client.connected()) {
    String clientId = "ESP32-" + getDeviceID();
    Serial.print("Menghubungkan MQTT...");

    if (client.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
      Serial.println("Berhasil!");
      client.subscribe(TOPIC_CONTROL.c_str());
    } else {
      Serial.printf("Gagal (rc=%d). Retry 2 detik...\n", client.state());
      delay(2000);
    }
  }
}

// ================================================================
// 11. BLE CALLBACKS
// ================================================================

class MyCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    String value = pCharacteristic->getValue();
    if (value.length() > 0) {
      Serial.println("Terima data BLE...");
      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, value.c_str());

      if (!error) {
        String ssid = doc["ssid"];
        String pass = doc["pass"];
        preferences.begin("wifi-conf", false);
        preferences.putString("ssid", ssid);
        preferences.putString("pass", pass);
        preferences.end();
        Serial.println("WiFi tersimpan. Restart...");
        delay(1000);
        ESP.restart();
      }
    }
  }
};

class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) { deviceConnected = true; }
  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    BLEDevice::startAdvertising();
  }
};

// ================================================================
// 12. SETUP
// ================================================================

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);

  // --- Pin Mode ---
  pinMode(RESET_BTN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(MQ135_PIN, INPUT);
  pinMode(RELAY_LAMP, OUTPUT);
  pinMode(RELAY_POMPA_MINUM, OUTPUT);
  pinMode(RELAY_POMPA_SIRAM, OUTPUT);
  pinMode(RELAY_EXHAUST, OUTPUT);

  // --- Semua relay OFF saat boot (Active LOW = HIGH = OFF) ---
  digitalWrite(RELAY_LAMP, HIGH);
  digitalWrite(RELAY_POMPA_MINUM, HIGH);
  digitalWrite(RELAY_POMPA_SIRAM, HIGH);
  digitalWrite(RELAY_EXHAUST, HIGH);

  // --- Inisialisasi sensor ---
  dht.begin();

  // --- Setup topic MQTT ---
  setupTopics();

  // --- Coba connect WiFi dari NVS ---
  preferences.begin("wifi-conf", true);
  String ssid = preferences.getString("ssid", "");
  String pass = preferences.getString("pass", "");
  preferences.end();

  if (ssid != "") {
    Serial.println("WiFi config ditemukan: " + ssid);
    WiFi.begin(ssid.c_str(), pass.c_str());

    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 20) {
      delay(500);
      Serial.print(".");
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      retry++;
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
      wifiConnected = true;
      digitalWrite(LED_PIN, HIGH);
      Serial.println("WiFi Connected! IP: " + WiFi.localIP().toString());
      client.setServer(MQTT_BROKER, MQTT_PORT);
      client.setCallback(callback);
    }
  }

  // --- Fallback: Mode BLE jika WiFi gagal ---
  if (!wifiConnected) {
    Serial.println("WiFi gagal. Masuk mode BLE...");
    digitalWrite(LED_PIN, LOW);

    String devName = String(DEVICE_NAME_PREFIX) + getDeviceID();
    BLEDevice::init(devName.c_str());

    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(SERVICE_UUID);
    BLECharacteristic *pCharacteristic = pService->createCharacteristic(
      CHARACTERISTIC_UUID,
      BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR
    );
    pCharacteristic->setCallbacks(new MyCallbacks());

    pService->start();
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    BLEDevice::startAdvertising();
    Serial.println("BLE aktif. Nama: " + devName);
  }
}

// ================================================================
// 13. LOOP UTAMA (NON-BLOCKING)
// ================================================================

void loop() {
  // --- Factory Reset (tahan tombol 3 detik) ---
  if (digitalRead(RESET_BTN) == LOW) {
    long start = millis();
    while (digitalRead(RESET_BTN) == LOW) {
      if (millis() - start > 3000) {
        Serial.println("RESET PABRIK!");
        preferences.begin("wifi-conf", false);
        preferences.clear();
        preferences.end();
        ESP.restart();
      }
    }
  }

  // --- Mode WiFi + MQTT ---
  if (wifiConnected) {
    // Reconnect WiFi jika terputus
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi terputus! Reconnecting...");
      WiFi.reconnect();
      delay(5000);
      return;
    }

    // Reconnect MQTT jika terputus
    if (!client.connected()) {
      reconnectMQTT();
    }
    client.loop();  // WAJIB dipanggil terus agar MQTT tidak timeout

    unsigned long now = millis();

    // --- Otomatis Lampu via LDR (setiap 2 detik) ---
    if (now - lastLdrCheck > INTERVAL_BACA_LDR) {
      lastLdrCheck = now;
      if (modeLampuOtomatis) {
        // Gelap (HIGH) = lampu nyala (LOW), Terang (LOW) = lampu mati (HIGH)
        digitalWrite(RELAY_LAMP, digitalRead(LDR_PIN) == HIGH ? LOW : HIGH);
      }
    }

    // --- Publish Data Sensor (setiap 30 detik) ---
    if (now - lastSensorPublish > INTERVAL_KIRIM_SENSOR) {
      lastSensorPublish = now;

      String payload = bacaSensor();

      if (client.connected()) {
        bool ok = client.publish(TOPIC_DATA.c_str(), payload.c_str());
        if (ok) {
          Serial.println("Terkirim: " + payload);
        } else {
          Serial.println("Gagal publish! Cek koneksi MQTT.");
        }
      }
    }
  }
}
```

### Catatan Penting tentang Kode

1. **Switch DHT22/DHT11:** Ubah baris `#define DHT_TYPE DHT22` menjadi `#define DHT_TYPE DHT11` jika mengganti sensor. Tidak perlu ubah kode lain.

2. **Semua relay Active LOW:** `LOW` = nyala, `HIGH` = mati. Saat boot, semua relay di-set `HIGH` (mati) untuk keamanan.

3. **Non-blocking:** Tidak ada `delay()` di loop utama (kecuali saat reconnect WiFi/MQTT yang memang perlu menunggu). Semua timing menggunakan `millis()`.

4. **BLE dan WiFi tidak bisa aktif bersamaan** di kode ini. BLE hanya aktif jika WiFi gagal connect saat boot.

5. **Lampu otomatis** bisa di-override dari Flutter app. Setelah menerima control command `"lampu"`, mode otomatis dinonaktifkan sampai ESP32 di-restart.

6. **`pakan_otomatis`** diabaikan di callback karena tidak ada hardware servo/load cell.

---

## 11. Testing & Validasi

### 11.1 Test Publish dengan mosquitto_pub (Simulasi ESP32)

Install mosquitto client di komputer Anda:

```bash
# Ubuntu/Debian
sudo apt install mosquitto-clients

# macOS
brew install mosquitto
```

**Test publish data sensor (simulasi ESP32):**

```bash
mosquitto_pub \
  -h 43.153.201.137 \
  -p 1883 \
  -u "device_user" \
  -P "pkl_pcb_iot_bagus_2026" \
  -t "devices/AABBCCDDEEFF/data" \
  -m '{"temperature":28.5,"humidity":72.0,"ammonia":15.0,"light_level":1}'
```

**Test control command (simulasi backend):**

```bash
mosquitto_pub \
  -h 43.153.201.137 \
  -p 1883 \
  -u "device_user" \
  -P "pkl_pcb_iot_bagus_2026" \
  -t "devices/AABBCCDDEEFF/control" \
  -m '{"component":"lampu","state":"ON"}'
```

### 11.2 Monitor Topic dengan mosquitto_sub

```bash
# Monitor SEMUA topic devices (sensor data + control)
mosquitto_sub \
  -h 43.153.201.137 \
  -p 1883 \
  -u "device_user" \
  -P "pkl_pcb_iot_bagus_2026" \
  -t "devices/#" \
  -v

# Monitor hanya sensor data dari device tertentu
mosquitto_sub \
  -h 43.153.201.137 \
  -p 1883 \
  -u "device_user" \
  -P "pkl_pcb_iot_bagus_2026" \
  -t "devices/AABBCCDDEEFF/data"
```

**Contoh output:**

```
devices/AABBCCDDEEFF/data {"temperature":28.5,"humidity":72.0,"ammonia":15.0,"light_level":1}
devices/AABBCCDDEEFF/control {"component":"lampu","state":"ON"}
```

### 11.3 Cek Device Status via API

```bash
# Cek apakah device online/offline
curl -s -H "Authorization: Bearer <JWT_TOKEN>" \
  "{{BASE_URL}}/api/devices/{device_id}/status" | python3 -m json.tool
```

**Response jika online:**

```json
{
  "device_id": "a1b2c3d4-...",
  "is_online": true,
  "last_seen": "2026-04-27T10:30:00Z",
  "seconds_since_last_seen": 15
}
```

**Response jika offline:**

```json
{
  "device_id": "a1b2c3d4-...",
  "is_online": false,
  "last_seen": "2026-04-27T10:25:00Z",
  "seconds_since_last_seen": 315
}
```

### 11.4 Cek Sensor Logs via API

```bash
# Ambil 5 log sensor terbaru
curl -s -H "Authorization: Bearer <JWT_TOKEN>" \
  "{{BASE_URL}}/api/devices/{device_id}/logs?page=1&limit=5" | python3 -m json.tool
```

**Response:**

```json
{
  "data": [
    {
      "id": 12345,
      "temperature": 28.5,
      "humidity": 72.0,
      "ammonia": 15.0,
      "is_alert": false,
      "alert_message": null,
      "timestamp": "2026-04-27T10:30:00Z"
    }
  ],
  "total": 500,
  "page": 1,
  "limit": 5,
  "total_pages": 100
}
```

### 11.5 Test Control Command via API

```bash
# Nyalakan lampu
curl -X POST "{{BASE_URL}}/api/devices/{device_id}/control" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"component": "lampu", "state": true}'

# Nyalakan exhaust fan
curl -X POST "{{BASE_URL}}/api/devices/{device_id}/control" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"component": "exhaust_fan", "state": true}'
```

### 11.6 Checklist Validasi End-to-End

Gunakan checklist ini untuk memastikan integrasi hardware-backend berjalan sempurna:

| # | Test Case | Cara Verifikasi | Status |
|:-:|-----------|-----------------|:------:|
| 1 | ESP32 connect WiFi | Serial Monitor: `"WiFi Connected!"` | [ ] |
| 2 | ESP32 connect MQTT | Serial Monitor: `"Berhasil!"` | [ ] |
| 3 | Data sensor terkirim | Serial Monitor: `"Terkirim: {...}"` | [ ] |
| 4 | Backend terima data | Docker log: `"Data masuk & Heartbeat updated"` | [ ] |
| 5 | Device status online | API: `GET /devices/{id}/status` → `is_online: true` | [ ] |
| 6 | Sensor logs tersimpan | API: `GET /devices/{id}/logs` → data muncul | [ ] |
| 7 | Control lampu ON | API: `POST /control` → relay lampu nyala | [ ] |
| 8 | Control lampu OFF | API: `POST /control` → relay lampu mati | [ ] |
| 9 | Control pompa ON/OFF | API: `POST /control` → relay pompa toggle | [ ] |
| 10 | Control kipas ON/OFF | API: `POST /control` → relay kipas toggle | [ ] |
| 11 | Control exhaust ON/OFF | API: `POST /control` → relay exhaust toggle | [ ] |
| 12 | Lampu otomatis (gelap) | Tutup LDR → lampu nyala otomatis | [ ] |
| 13 | Lampu otomatis (terang) | Buka LDR → lampu mati otomatis | [ ] |
| 14 | Override lampu manual | Kirim control `"lampu"` → mode otomatis off | [ ] |
| 15 | Alert suhu panas | Set suhu > 35C → backend kirim FCM push | [ ] |
| 16 | Alert amonia tinggi | Set ammonia > 20 ppm → backend kirim FCM push | [ ] |
| 17 | Factory reset | Tahan tombol 3 detik → ESP32 restart, masuk BLE | [ ] |
| 18 | BLE provisioning | Kirim WiFi via Flutter → ESP32 connect WiFi | [ ] |
| 19 | Reconnect WiFi | Matikan router → nyalakan → ESP32 reconnect | [ ] |
| 20 | Reconnect MQTT | Restart Mosquitto → ESP32 reconnect + resubscribe | [ ] |

---

## 12. Rekomendasi Pengembangan Lanjutan

### 12.1 Auto-Trigger Exhaust Fan

Saat ini exhaust fan hanya bisa dikontrol manual dari Flutter app. Rekomendasi: tambahkan logika otomatis di ESP32:

```cpp
// Di dalam loop, setelah baca sensor:
if (ammonia > 20.0 || suhu > 35.0) {
  digitalWrite(RELAY_EXHAUST, LOW);   // Nyalakan exhaust
} else {
  digitalWrite(RELAY_EXHAUST, HIGH);  // Matikan exhaust
}
```

> **Alternatif:** Implementasi di backend — saat MQTT Worker mendeteksi alert, backend otomatis publish control command `{"component":"exhaust_fan","state":"ON"}` ke ESP32.

### 12.2 Watchdog Timer

Tambahkan watchdog timer untuk auto-restart ESP32 jika hang:

```cpp
#include <esp_task_wdt.h>

void setup() {
  esp_task_wdt_init(30, true);  // Timeout 30 detik
  esp_task_wdt_add(NULL);
}

void loop() {
  esp_task_wdt_reset();  // Reset watchdog setiap loop
  // ... kode lain ...
}
```

Jika `loop()` tidak berjalan selama 30 detik (hang), ESP32 akan restart otomatis.

### 12.3 OTA Update (Over-The-Air)

Update firmware ESP32 via WiFi tanpa perlu colok USB:

```cpp
#include <ArduinoOTA.h>

void setup() {
  // ... setelah WiFi connected ...
  ArduinoOTA.setHostname("pcb-kandang-utara");
  ArduinoOTA.setPassword("ota_password");
  ArduinoOTA.begin();
}

void loop() {
  ArduinoOTA.handle();
  // ... kode lain ...
}
```

Upload dari Arduino IDE: **Tools → Port → pilih network port ESP32**.

### 12.4 Deep Sleep Mode (Hemat Daya)

Jika ESP32 menggunakan battery/solar panel, gunakan deep sleep untuk hemat daya:

```cpp
// Publish data, lalu tidur 5 menit
esp_sleep_enable_timer_wakeup(5 * 60 * 1000000);  // 5 menit dalam microseconds
esp_deep_sleep_start();
```

> **Catatan:** Deep sleep akan mematikan WiFi dan MQTT. ESP32 harus reconnect setiap bangun. Tidak cocok untuk monitoring real-time, tapi cocok untuk monitoring periodik.

### 12.5 Perubahan Backend yang Dibutuhkan

Untuk integrasi penuh dengan hardware baru ini, backend perlu diperbarui:

| # | Perubahan | File | Prioritas |
|:-:|-----------|------|:---------:|
| 1 | Tambah field `light_level` ke model `SensorLog` | `app/models/device.py` | **Wajib** |
| 2 | Buat migration Alembic untuk `light_level` | `alembic/versions/006_*.py` | **Wajib** |
| 3 | Update validasi `validate_sensor_data()` | `app/mqtt/mqtt_worker.py` | **Wajib** |
| 4 | Update `on_message()` untuk simpan `light_level` | `app/mqtt/mqtt_worker.py` | **Wajib** |
| 5 | Tambah `"exhaust_fan"` ke schema `DeviceControl` | `app/schemas/device.py` | **Wajib** |
| 6 | Tambah `light_level` ke schema `LogResponse` | `app/schemas/sensor.py` | Opsional |
| 7 | Update `API_CONTRACT.md` | `API_CONTRACT.md` | Opsional |
| 8 | Update `README.md` section Hardware | `README.md` | Opsional |

---

## Lampiran: Ringkasan Cepat

### Payload Sensor (ESP32 → Backend)

```json
{"temperature": 30.5, "humidity": 75.0, "ammonia": 12.5, "light_level": 1}
```

### Control Command (Backend → ESP32)

```json
{"component": "lampu", "state": "ON"}
```

### Topic MQTT

```
Publish  : devices/{MAC_TANPA_COLON}/data
Subscribe: devices/{MAC_TANPA_COLON}/control
```

### Pin GPIO

```
GPIO  0 = Reset Button     GPIO 17 = Relay 1 (Lampu)
GPIO  2 = LED Status       GPIO  5 = Relay 2 (Pompa Minum)
GPIO  4 = DHT22/DHT11      GPIO 18 = Relay 3 (Pompa Siram)
GPIO 16 = LDR              GPIO 19 = Relay 4 (Exhaust Fan)
GPIO 34 = MQ-135 (ADC)
```

### Timing

```
Publish sensor  : setiap 30 detik
Cek LDR         : setiap 2 detik
Heartbeat timeout: 120 detik (backend anggap offline)
Alert cooldown  : 5 menit per device
```
