# PKL PCB - Smart Kandang IoT Platform

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)
![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-3C5280?style=for-the-badge&logo=eclipse-mosquitto)
![Firebase](https://img.shields.io/badge/Firebase-Auth-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)

Platform IoT terintegrasi untuk monitoring dan controlling kandang ayam pintar. Backend API (FastAPI) + Admin Dashboard (React) + Landing Page dalam satu container Docker.

Project ini dibuat untuk keperluan **Praktik Kerja Lapangan (PKL)**.

---

## Arsitektur

```
Internet
    |
Cloudflare (DNS + Proxy)
    |
VPS (Nginx Proxy Manager)
    |
    +-- pcb_pkl_backend (port 80)
    |     |
    |     +-- Nginx
    |     |     +-- /           --> React (Landing Page)
    |     |     +-- /admin/*    --> React (Admin Dashboard)
    |     |     +-- /api/*      --> Uvicorn (FastAPI)
    |     |     +-- /docs       --> Swagger UI
    |     |
    |     +-- Uvicorn (2 workers, non-root)
    |           +-- FastAPI Backend
    |
    +-- pcb_pkl_postgres (PostgreSQL 15)
    +-- pcb_pkl_mosquitto (MQTT Broker, port 1883)
    +-- pcb_pkl_mqtt_worker (MQTT Subscriber)
```

Semua service dikelola oleh Docker Compose. Backend + Frontend digabung dalam satu container menggunakan **Supervisord** (Nginx + Uvicorn).

---

## Fitur

### Backend API
- **Firebase Authentication** -- Login via Firebase, JWT lokal untuk proteksi endpoint
- **Role-Based Access Control** -- 2 role: `admin` dan `user`, disimpan di database
- **Device Management** -- Register (admin), claim via QR (user), unclaim
- **Real-time Monitoring** -- Data sensor (suhu, kelembaban, amonia) via MQTT
- **Smart Alerting** -- Deteksi otomatis suhu/amonia berbahaya (threshold configurable)
- **Remote Control** -- Kontrol kipas, lampu, pompa, pakan via MQTT
- **Daily Statistics** -- Agregasi statistik harian per device
- **Rate Limiting** -- Proteksi DDoS dengan shared rate limiter
- **Request ID Tracing** -- Setiap request mendapat ID unik untuk debugging

### Admin Dashboard (Web)
- **Login** -- Firebase email/password authentication
- **Dashboard** -- Overview jumlah user, device, status online (dengan animated counters dan chart)
- **Kelola User** -- Tabel user dengan search, promote/demote role, sync dari Firebase
- **Kelola Device** -- Register device baru (MAC address), lihat unclaimed devices
- **Responsive** -- Mobile-friendly dengan collapsible sidebar

### Landing Page
- **Hero Section** -- Dengan floating sensor cards dan scroll indicator
- **Features** -- Dibagi 2 kategori: Monitoring dan Otomatisasi
- **Animasi** -- Framer Motion untuk scroll reveal, hover effects, page transitions

---

## Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic 2.x |
| Frontend | React 19, Vite, Tailwind CSS v4, shadcn/ui, Framer Motion |
| Database | PostgreSQL 15, Alembic (migration) |
| Auth | Firebase Admin SDK (server), Firebase Web SDK (client), PyJWT |
| MQTT | Eclipse Mosquitto 2.x, paho-mqtt |
| Charts | Recharts |
| Container | Docker, Docker Compose, Supervisord, Nginx |
| CI/CD | GitHub Actions (auto-deploy ke VPS) |
| Proxy | Nginx Proxy Manager, Cloudflare |

---

## Struktur Project

```
pkl-pcb/
├── app/                          # Backend FastAPI
│   ├── core/
│   │   ├── config.py             # Pydantic Settings (.env)
│   │   ├── security.py           # JWT create & verify (PyJWT)
│   │   ├── limiter.py            # Shared rate limiter instance
│   │   ├── logging_config.py     # Logging dengan Request ID filter
│   │   └── request_context.py    # ContextVars untuk Request ID
│   ├── models/
│   │   ├── user.py               # Model User + UserRole enum
│   │   └── device.py             # Model Device + SensorLog
│   ├── routers/
│   │   ├── auth.py               # POST /api/auth/firebase/login
│   │   ├── user.py               # GET/PATCH/DELETE /api/users/me, PATCH role
│   │   ├── device.py             # CRUD devices, logs, alerts, control, stats
│   │   └── admin.py              # GET /api/admin/stats, users, sync-firebase
│   ├── schemas/
│   │   ├── user.py               # UserResponse, UpdateUserRole, UpdateUserName
│   │   ├── device.py             # DeviceClaim, DeviceResponse, DailyStats
│   │   └── sensor.py             # LogResponse
│   ├── mqtt/
│   │   ├── mqtt_worker.py        # MQTT subscriber + data ingestion
│   │   └── publisher.py          # MQTT publisher untuk kontrol device
│   ├── database.py               # SQLAlchemy engine & session
│   ├── dependencies.py           # Auth dependencies (get_current_user, get_current_admin)
│   └── main.py                   # FastAPI app, middleware, lifespan
├── pcb-landing-page/             # Frontend React
│   ├── src/
│   │   ├── components/           # Landing page components (Navbar, Hero, Features, Footer)
│   │   │   ├── ui/               # shadcn components (Button, Card, Badge, Table, Dialog, etc.)
│   │   │   └── shared/           # AnimatedCounter, PageTransition, Skeleton
│   │   ├── admin/
│   │   │   ├── pages/            # LoginPage, DashboardPage, UsersPage, DevicesPage
│   │   │   ├── components/       # AdminLayout, Sidebar, AdminGuard
│   │   │   └── hooks/            # useAuth (Firebase + JWT)
│   │   └── lib/
│   │       ├── api.js            # Axios API client
│   │       ├── firebase.js       # Firebase web config
│   │       └── utils.js          # Tailwind class merger
│   └── package.json
├── alembic/                      # Database migrations
│   └── versions/
│       └── 001_add_role_column_to_users.py
├── scripts/
│   ├── backup_db.sh              # Backup PostgreSQL ke .sql.gz
│   └── restore_db.sh             # Restore dari backup
├── tests/                        # Unit tests (71 test cases)
│   ├── conftest.py               # Fixtures & SQLite test database
│   ├── test_security.py          # JWT token tests
│   ├── test_device.py            # Device endpoint tests
│   ├── test_stats.py             # Daily statistics tests
│   └── test_user.py              # User, role, admin access tests
├── Dockerfile                    # Multi-stage: Node build + Python + Nginx
├── docker-compose.yml            # Base compose (4 services)
├── docker-compose.override.yml   # Development overrides (hot-reload)
├── docker-compose.prod.yml       # Production overrides (external volume)
├── nginx.conf                    # Nginx config (SPA + API proxy)
├── supervisord.conf              # Process manager (Nginx + Uvicorn)
├── requirements.txt              # Python dependencies
├── alembic.ini                   # Alembic config
└── .github/workflows/deploy.yml  # CI/CD pipeline
```

---

## Quick Start (Development)

### 1. Clone Repository

```bash
git clone https://github.com/Bagus-DevLab/PKL_PCB_BACKEND.git
cd pkl-pcb
```

### 2. Setup Environment

```bash
# Copy .env template
cp .env.example .env
# Edit .env dengan credentials kamu
```

### 3. Jalankan Backend (Docker)

```bash
# Development mode (dengan hot-reload)
docker compose up -d --build

# Cek status
docker ps
curl http://localhost:8001/api/health
```

### 4. Jalankan Frontend (Vite Dev Server)

```bash
cd pcb-landing-page
cp .env.example .env
# Edit .env dengan Firebase web config
npm install
npm run dev
```

Buka:
- Landing page: `http://localhost:5173/`
- Admin login: `http://localhost:5173/admin/login`
- API docs: `http://localhost:8001/docs`

### 5. Jalankan Migration

```bash
docker compose exec backend alembic upgrade head
```

---

## Environment Variables

### Backend `.env` (Root)

| Variable | Deskripsi | Contoh |
|----------|-----------|--------|
| `ENVIRONMENT` | Mode aplikasi | `development` / `production` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@postgres:5432/db` |
| `SECRET_KEY` | JWT signing key | Random string 32+ karakter |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL | `10080` (7 hari) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Dari Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | Dari Google Cloud Console |
| `BASE_URL` | Backend base URL | `https://pcb.my.id` |
| `MQTT_BROKER` | MQTT broker hostname | `mosquitto` (Docker network) |
| `MQTT_PORT` | MQTT broker port | `1883` |
| `MQTT_TOPIC` | MQTT subscription topic | `devices/+/data` |
| `MQTT_USERNAME` | MQTT auth username | `device_user` |
| `MQTT_PASSWORD` | MQTT auth password | Password kamu |
| `CORS_ORIGINS` | Allowed origins | `https://pcb.my.id` atau `https://a.com,https://b.com` |
| `INITIAL_ADMIN_EMAIL` | Email admin pertama | `admin@example.com` |
| `ALERT_TEMP_MAX` | Threshold suhu maks | `35.0` |
| `ALERT_TEMP_MIN` | Threshold suhu min | `20.0` |
| `ALERT_AMMONIA_MAX` | Threshold amonia maks | `20.0` |
| `DEVICE_ONLINE_TIMEOUT_SECONDS` | Timeout heartbeat | `120` (2 menit) |
| `VITE_FIREBASE_API_KEY` | Firebase web API key | Dari Firebase Console |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase auth domain | `project.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Firebase project ID | `your-project-id` |
| `VITE_FIREBASE_STORAGE_BUCKET` | Firebase storage | `project.appspot.com` |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Firebase sender ID | `123456789` |
| `VITE_FIREBASE_APP_ID` | Firebase app ID | `1:123:web:abc` |

`CORS_ORIGINS` mendukung 3 format:
- JSON array: `["https://a.com","https://b.com"]`
- Comma-separated: `https://a.com,https://b.com`
- Single origin: `https://a.com`

### Frontend `.env` (pcb-landing-page/) -- Development Only

| Variable | Deskripsi | Contoh |
|----------|-----------|--------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8001/api` |
| `VITE_FIREBASE_*` | Firebase config (sama dengan root) | Dari Firebase Console |

---

## API Endpoints

Semua endpoint di-prefix dengan `/api`.

### Public

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/auth/firebase/login` | Login via Firebase token |

### User (Authenticated)

| Method | Endpoint | Deskripsi | Rate Limit |
|--------|----------|-----------|------------|
| `GET` | `/api/users/me` | Get profil user | - |
| `PATCH` | `/api/users/me` | Update nama | - |
| `DELETE` | `/api/users/me` | Hapus akun | - |
| `GET` | `/api/devices/` | List devices milik user | 30/min |
| `POST` | `/api/devices/claim` | Klaim device (scan QR) | 10/min |
| `POST` | `/api/devices/{id}/unclaim` | Lepas kepemilikan | 10/min |
| `GET` | `/api/devices/{id}/logs` | History data sensor | 60/min |
| `GET` | `/api/devices/{id}/alerts` | Riwayat alert | 60/min |
| `GET` | `/api/devices/{id}/stats/daily` | Statistik harian | 30/min |
| `POST` | `/api/devices/{id}/control` | Remote control device | 30/min |
| `GET` | `/api/devices/{id}/status` | Cek online/offline | 60/min |

### Admin Only

| Method | Endpoint | Deskripsi | Rate Limit |
|--------|----------|-----------|------------|
| `POST` | `/api/devices/register` | Register device baru (MAC) | 20/min |
| `GET` | `/api/devices/unclaimed` | List device belum diklaim | 30/min |
| `PATCH` | `/api/users/{id}/role` | Ubah role user | 10/min |
| `GET` | `/api/admin/stats` | Dashboard overview | 30/min |
| `GET` | `/api/admin/users` | List semua user | 30/min |
| `POST` | `/api/admin/sync-firebase-users` | Sync user dari Firebase | 5/min |

---

## Hardware Integration (ESP32)

### Kirim Data Sensor (Publish)

Topic: `devices/{MAC_ADDRESS}/data`

```json
{
  "temperature": 30.5,
  "humidity": 75.0,
  "ammonia": 12.5
}
```

Semua 3 field wajib ada. Data divalidasi:
- Suhu: -40 s/d 80 (derajat C)
- Kelembaban: 0 s/d 100 (%)
- Amonia: 0 s/d 500 (ppm)

### Terima Perintah Kontrol (Subscribe)

Topic: `devices/{MAC_ADDRESS}/control`

```json
{
  "component": "kipas",
  "state": true
}
```

Komponen valid: `kipas`, `lampu`, `pompa`, `pakan_otomatis`

---

## Testing

```bash
# Aktifkan virtual environment
source .venv/bin/activate

# Jalankan semua test
pytest -v

# Test spesifik
pytest tests/test_device.py -v
pytest tests/test_user.py -v
pytest tests/test_stats.py -v
pytest tests/test_security.py -v
```

**71 test cases** mencakup:

| Module | Tests | Cakupan |
|--------|-------|---------|
| `test_security.py` | 8 | JWT create/verify, expired, invalid |
| `test_device.py` | 20 | Claim, unclaim, logs, alerts, control |
| `test_stats.py` | 23 | Daily statistics, parameter validation, security |
| `test_user.py` | 20 | Profile, role management, admin access, health check |

---

## Database Backup & Restore

```bash
# Backup manual
./scripts/backup_db.sh

# Restore dari backup
./scripts/restore_db.sh backups/backup_2026-04-24_12-00-00.sql.gz
```

Backup otomatis via cron (setiap Minggu jam 3 pagi) sudah di-setup di VPS production.

---

## Deploy ke Production

### CI/CD (GitHub Actions)

Setiap push ke branch `main` otomatis trigger deploy:

1. SCP project ke VPS `/opt/api-pcb`
2. Inject `.env` dari GitHub Secret `ENV_FILE`
3. Backup database sebelum deploy
4. Build Docker image (multi-stage)
5. Start containers dengan `docker-compose.prod.yml`
6. Health check (max 60 detik)
7. Run Alembic migration
8. Cleanup image lama

### GitHub Secrets

| Secret | Isi |
|--------|-----|
| `ENV_FILE` | Seluruh isi file `.env` production |
| `VPS_HOST` | IP address VPS |
| `VPS_USERNAME` | SSH username (`root`) |
| `VPS_SSH_KEY` | SSH private key |

### Manual Deploy

```bash
# Production (tanpa override, dengan volume protection)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Jalankan migration
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Production Checklist

- [ ] `ENVIRONMENT=production` di `.env`
- [ ] `SECRET_KEY` menggunakan random string 32+ karakter
- [ ] `BASE_URL` menggunakan domain production
- [ ] `CORS_ORIGINS` menggunakan domain production
- [ ] `INITIAL_ADMIN_EMAIL` di-set untuk bootstrap admin pertama
- [ ] `VITE_FIREBASE_*` di-set untuk admin dashboard
- [ ] `firebase-adminsdk.json` ada di root project
- [ ] MQTT authentication aktif (username/password)
- [ ] Nginx Proxy Manager forward ke `pcb_pkl_backend:80`
- [ ] Cloudflare DNS mengarah ke IP VPS
- [ ] Database volume `api-pcb_postgres_data` sudah ada (external)
- [ ] Backup cron sudah aktif

---

## Troubleshooting

| Problem | Solusi |
|---------|--------|
| Backend crash saat startup | Cek `.env` lengkap: `docker logs pcb_pkl_backend --tail 30` |
| `CORS_ORIGINS` parsing error | Gunakan format tanpa bracket: `CORS_ORIGINS=https://pcb.my.id` |
| `column users.role does not exist` | Jalankan migration: `alembic upgrade head` |
| 502 Bad Gateway dari NPM | NPM harus forward ke container name `pcb_pkl_backend` port `80`, bukan `127.0.0.1` |
| Admin login gagal | Pastikan `VITE_FIREBASE_*` ada di `.env` saat Docker build |
| MQTT "Not authorized" | Cek `MQTT_USERNAME`/`MQTT_PASSWORD` di `.env` |
| Data sensor ditolak | Semua 3 field wajib: `temperature`, `humidity`, `ammonia` |
| Device selalu offline | Heartbeat timeout: 2 menit (configurable via `DEVICE_ONLINE_TIMEOUT_SECONDS`) |
| Flutter app 404 | Semua API endpoint sekarang di-prefix `/api/` |

### Cek Logs

```bash
# Backend
docker logs pcb_pkl_backend --tail 50

# MQTT Worker
docker logs pcb_pkl_mqtt_worker --tail 50

# Semua service
docker compose logs -f
```

---

## Author

**Bagus Ardiansyah** -- Backend & Frontend Engineer
Praktik Kerja Lapangan (PKL) 2026

## License

Project ini dibuat untuk keperluan pendidikan (PKL).
