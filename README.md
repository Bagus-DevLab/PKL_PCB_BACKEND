# Smart Chicken Box (PCB) &mdash; IoT Backend API

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-Mosquitto_2-3C5280?style=for-the-badge&logo=eclipse-mosquitto&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-Auth_+_FCM-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)
![Tests](https://img.shields.io/badge/Tests-117_Passed-2ea44f?style=for-the-badge)

A production-hardened IoT backend for monitoring and controlling smart chicken coops. Built with FastAPI, PostgreSQL, MQTT, and WebSockets &mdash; engineered for resource-constrained VPS deployments (2 GB RAM, 2 cores).

Powers real-time sensor telemetry from ESP32 microcontrollers, a 5-tier role-based access control hierarchy, push-notification alerting, and a React admin dashboard &mdash; all served from a single Docker container behind Nginx.

---

## Architecture

```
  ESP32 Devices                       Flutter Mobile App
       |                                     |
       | MQTT (QoS 1)                        | HTTPS / WebSocket
       v                                     v
+-----------+    +----------------------------------------------------+
| Mosquitto |    |              Docker Compose (VPS)                   |
|   MQTT    |    |                                                     |
|  Broker   |<-->|  +----------------------------------------------+  |
|  :1883    |    |  |  pcb_pkl_backend  (Supervisord)               |  |
+-----------+    |  |                                               |  |
       ^         |  |  Nginx :80                                    |  |
       |         |  |    /           -> React SPA (static files)    |  |
       |         |  |    /admin/*    -> React Admin Dashboard       |  |
       |         |  |    /api/*      -> Uvicorn (FastAPI)           |  |
       |         |  |    /api/ws/*   -> WebSocket (upgrade)         |  |
       |         |  |                                               |  |
       |         |  |  Uvicorn :8000 (2 workers)                    |  |
       |         |  |    FastAPI Application                        |  |
       |         |  +----------------------------------------------+  |
       |         |                                                     |
       |         |  +------------------+  +-------------------------+  |
       |         |  | pcb_pkl_postgres |  | pcb_pkl_mqtt_worker     |  |
       +---------|--| PostgreSQL 15    |  | Sensor data ingestion   |  |
                 |  | :5432            |  | Alert detection + FCM   |  |
                 |  +------------------+  +-------------------------+  |
                 +----------------------------------------------------+
```

**Data flow:** ESP32 publishes sensor readings (temperature, humidity, ammonia) to Mosquitto via MQTT. The dedicated MQTT Worker subscribes, validates payloads, persists data to PostgreSQL, and fires FCM push notifications when thresholds are breached. The Flutter app authenticates through Firebase, receives a local JWT, and streams live data over WebSockets. Admins control devices (fans, lights, pumps, feeders) through REST endpoints that publish MQTT commands back to the ESP32.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI 0.115, Uvicorn, Pydantic 2.9 |
| **Database** | PostgreSQL 15, SQLAlchemy 2.0, Alembic |
| **Authentication** | Firebase Admin SDK, PyJWT (HS256) |
| **Messaging** | Eclipse Mosquitto 2, paho-mqtt 2.1 |
| **Push Notifications** | Firebase Cloud Messaging (FCM) |
| **Frontend** | React 19, Vite 7, Tailwind CSS v4, shadcn/ui |
| **Infrastructure** | Docker, Docker Compose, Supervisord, Nginx |
| **Rate Limiting** | slowapi (per-endpoint, configurable) |
| **CI/CD** | GitHub Actions &rarr; SCP &rarr; VPS auto-deploy |
| **Testing** | pytest &mdash; 117 test cases, SQLite in-memory |

---

## Key Features

### Real-Time IoT Telemetry

- **Bi-directional MQTT** &mdash; ESP32 devices publish sensor data and subscribe to control commands via QoS 1.
- **WebSocket streaming** &mdash; Live sensor data pushed to connected clients every 3 seconds with automatic device-deletion detection and anti-zombie connection cleanup.
- **Configurable alert thresholds** &mdash; Temperature and ammonia limits set via environment variables. Breaches trigger instant FCM push notifications with a per-device cooldown.

### Advanced Role-Based Access Control

Five hierarchical roles with granular, device-level permissions:

```
super_admin > admin > operator > viewer > user
```

| Role | Capabilities |
|------|-------------|
| **Super Admin** | Full system access. Register devices, manage all roles, sync Firebase users. |
| **Admin** | Claim devices, assign operators/viewers to owned devices, view and control. |
| **Operator** | View and control assigned devices (fans, lights, pumps, feeders). |
| **Viewer** | Read-only access to assigned device data. |
| **User** | Default on registration. No device access until assigned by an admin. |

Device ownership is enforced at every layer &mdash; REST endpoints, WebSocket connections, and MQTT control commands all validate access through a unified dependency chain.

### Enterprise Resilience (Optimized for 2 GB RAM)

| Optimization | Detail |
|-------------|--------|
| **Connection pool tuning** | `pool_size=3, max_overflow=7, pool_timeout=10s, pool_recycle=1800s` with `pool_pre_ping` for stale-connection recovery. |
| **Batched cleanup** | Sensor-log retention deletes in batches of 1 000 rows to avoid long-running locks and WAL bloat. |
| **MQTT device cache** | In-memory MAC &rarr; device-ID cache with 5-minute TTL eliminates a DB lookup on every message. |
| **Graceful shutdown** | SIGTERM handler cleanly disconnects the MQTT client &mdash; no orphaned broker sessions. |
| **Bad-payload rejection** | Strict topic validation (`devices/{mac}/data`), UTF-8 enforcement, JSON schema checks, and sensor-range bounds. |
| **Anti-zombie WebSockets** | Broken connections break the polling loop immediately. Device deletion or unclaim triggers proactive WebSocket closure via `ws_manager`. |
| **Dashboard query consolidation** | Admin stats use `GROUP BY` + conditional `CASE` aggregation &mdash; 3 queries instead of 10. |
| **N+1 query elimination** | Device assignments use `joinedload` for single-query eager loading. |
| **Non-blocking auth** | Auth dependencies are synchronous `def` (not `async def`) so FastAPI runs them in a threadpool instead of blocking the event loop. |

### Security Hardening

| Protection | Implementation |
|-----------|---------------|
| **Rate limiting** | Every endpoint carries a `slowapi` limit (5 &ndash; 60 req/min depending on sensitivity). |
| **Payload size limits** | Nginx `client_max_body_size 1m` + Pydantic `Field(max_length=...)` on all string inputs. |
| **JWT active-state validation** | Token verification checks `is_active` on every request &mdash; deactivated users are rejected immediately. |
| **Race-condition protection** | `SELECT ... FOR UPDATE` on device claiming; `IntegrityError` catch-and-retry on first-login user creation. |
| **Notification cooldown** | Max 1 FCM push per device per 5 minutes via `time.monotonic()` &mdash; prevents alert spam. |
| **Error sanitization** | Internal exception details are logged server-side but never returned to clients. |
| **CORS configuration** | Supports JSON array, comma-separated, and single-origin formats with an explicit allowlist. |
| **Request-ID tracing** | Every request receives a unique ID via the `X-Request-ID` header for end-to-end debugging. |

### Database Optimization

| Optimization | Detail |
|-------------|--------|
| **Composite B-tree index** | `ix_sensor_logs_device_timestamp` on `(device_id, timestamp DESC)` &mdash; covers the most frequent query pattern. |
| **CASCADE foreign keys** | `SensorLog.device_id` and `DeviceAssignment.device_id` use `ondelete="CASCADE"` for safe device deletion. |
| **Migration chain** | `001_add_role` &rarr; `002_role_hierarchy` &rarr; `003_fcm_tokens` &rarr; `004_cascade_sensor_log` &rarr; `005_composite_index` |

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| [Docker](https://docs.docker.com/get-docker/) + Docker Compose | v2+ |
| [Python](https://www.python.org/downloads/) | 3.12 (local dev / testing) |
| [Node.js](https://nodejs.org/) | 20+ (frontend development) |
| [Firebase](https://console.firebase.google.com/) project | Authentication enabled |
| `firebase-adminsdk.json` | Service-account key file |

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/pkl-pcb.git
cd pkl-pcb
```

### 2. Configure environment

```bash
cp .env.example .env
```

At minimum, set these three values:

```env
SECRET_KEY=your_random_64_char_string_here
INITIAL_ADMIN_EMAIL=your-email@example.com
POSTGRES_PASSWORD=a_strong_database_password
```

Place your Firebase service-account key at the project root:

```bash
cp /path/to/firebase-adminsdk.json ./firebase-adminsdk.json
```

### 3. Start all services

```bash
# Development (auto-loads docker-compose.override.yml with hot-reload)
docker compose up -d --build

# Verify containers are healthy
docker ps
```

### 4. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Verify

```bash
curl http://localhost:8001/api/health
# {"status":"healthy","database_alive":true}
```

API documentation (development only): <http://localhost:8001/docs>

### 6. Frontend development (optional)

```bash
cd pcb-landing-page && npm install && npm run dev
```

| URL | What |
|-----|------|
| `http://localhost:5173/` | Landing page |
| `http://localhost:5173/admin/login` | Admin dashboard |

### Production deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `ENVIRONMENT` | Yes | &mdash; | `development` or `production`. Controls docs visibility and auto-table creation. |
| `DATABASE_URL` | Yes | &mdash; | PostgreSQL connection string, e.g. `postgresql://user:pass@postgres:5432/db`. |
| `SECRET_KEY` | Yes | &mdash; | JWT signing key. Use a random string of 32+ characters. |
| `ALGORITHM` | No | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | &mdash; | JWT lifetime in minutes. Recommended: `10080` (7 days). |
| `POSTGRES_USER` | Yes | &mdash; | PostgreSQL username (Docker Compose). |
| `POSTGRES_PASSWORD` | Yes | &mdash; | PostgreSQL password (Docker Compose). |
| `POSTGRES_DB` | Yes | &mdash; | PostgreSQL database name (Docker Compose). |
| `MQTT_BROKER` | Yes | &mdash; | Broker hostname. Use `mosquitto` inside Docker. |
| `MQTT_PORT` | No | `1883` | Broker port. |
| `MQTT_TOPIC` | Yes | &mdash; | Subscription pattern. Use `devices/+/data`. |
| `MQTT_USERNAME` | Yes | &mdash; | Broker auth username (empty string for open dev). |
| `MQTT_PASSWORD` | Yes | &mdash; | Broker auth password (empty string for open dev). |
| `CORS_ORIGINS` | Yes | &mdash; | Allowed origins &mdash; JSON array, comma-separated, or single string. |
| `INITIAL_ADMIN_EMAIL` | No | `""` | Email auto-promoted to `super_admin` on first login. |
| `ALERT_TEMP_MAX` | No | `35.0` | Upper temperature threshold (&deg;C). |
| `ALERT_TEMP_MIN` | No | `20.0` | Lower temperature threshold (&deg;C). |
| `ALERT_AMMONIA_MAX` | No | `20.0` | Upper ammonia threshold (ppm). |
| `DEVICE_ONLINE_TIMEOUT_SECONDS` | No | `120` | Heartbeat window before a device is marked offline. |
| `SENSOR_LOG_RETENTION_DAYS` | No | `365` | Days to keep sensor logs. `0` = keep forever. |
| `VITE_FIREBASE_*` | Yes | &mdash; | Six Firebase web-config vars. Passed as Docker build args. |

---

## Project Structure

```
pkl-pcb/
├── app/                              # FastAPI backend
│   ├── core/                         #   Framework utilities
│   │   ├── config.py                 #     Pydantic Settings (.env validation)
│   │   ├── security.py               #     JWT creation & verification
│   │   ├── limiter.py                #     Shared slowapi rate-limiter instance
│   │   ├── notifications.py          #     FCM push sender + 5-min cooldown
│   │   ├── pagination.py             #     Reusable query pagination helper
│   │   ├── ws_manager.py             #     WebSocket connection manager
│   │   ├── logging_config.py         #     Structured logging with request ID
│   │   └── request_context.py        #     ContextVar for request tracing
│   ├── models/                       #   SQLAlchemy ORM models
│   │   ├── user.py                   #     User, UserRole (5-tier enum), FcmToken
│   │   └── device.py                 #     Device, SensorLog, DeviceAssignment
│   ├── routers/                      #   API endpoint handlers
│   │   ├── auth.py                   #     POST /auth/firebase/login
│   │   ├── user.py                   #     /users/me CRUD, role management, FCM tokens
│   │   ├── device.py                 #     Device CRUD, logs, alerts, control, assignments
│   │   ├── admin.py                  #     Dashboard stats, user list, Firebase sync, cleanup
│   │   └── ws.py                     #     WebSocket real-time sensor streaming
│   ├── schemas/                      #   Pydantic request / response schemas
│   │   ├── user.py                   #     UserResponse, UpdateUserRole, UpdateUserName
│   │   ├── device.py                 #     DeviceClaim, DeviceResponse, DailyStats
│   │   ├── sensor.py                 #     LogResponse
│   │   └── pagination.py             #     PaginatedResponse wrapper
│   ├── mqtt/                         #   MQTT subsystem
│   │   ├── mqtt_worker.py            #     Subscriber: ingest, validate, alert, cache
│   │   └── publisher.py              #     Publisher: device control commands
│   ├── database.py                   #   Engine, pool config, session factory
│   ├── dependencies.py               #   Auth: get_current_user, role checks, device access
│   └── main.py                       #   App init, lifespan, middleware, exception handlers
├── pcb-landing-page/                 # React frontend (landing + admin dashboard)
├── alembic/                          # Database migrations (5 versions)
├── tests/                            # pytest suite — 117 test cases
│   ├── conftest.py                   #   Fixtures, SQLite in-memory DB, test users
│   ├── test_device.py                #   49 tests — CRUD, claims, assignments, control
│   ├── test_security.py              #   8 tests — JWT creation, verification, expiry
│   ├── test_stats.py                 #   23 tests — daily statistics, validation, access
│   └── test_user.py                  #   37 tests — profile, roles, admin, FCM, cleanup
├── scripts/                          # backup_db.sh, restore_db.sh
├── mosquitto/                        # Broker config + password file
├── Dockerfile                        # Multi-stage: Node build → Python → Nginx
├── docker-compose.yml                # Base: backend, postgres, mosquitto, mqtt_worker
├── docker-compose.override.yml       # Dev: Uvicorn hot-reload, no Nginx
├── docker-compose.prod.yml           # Prod: external volumes, Supervisord
├── nginx.conf                        # SPA routing + API proxy + WebSocket upgrade
├── supervisord.conf                  # Process manager (Nginx + Uvicorn)
├── requirements.txt                  # Python dependencies
├── alembic.ini                       # Alembic configuration
└── .github/workflows/deploy.yml      # CI/CD — auto-deploy on push to main
```

---

## Testing

```bash
source .venv/bin/activate
pytest -v                          # all 117 tests
pytest tests/test_device.py -v     # device endpoints
pytest -k "test_admin_can" -v      # pattern match
```

| Module | Tests | Scope |
|--------|------:|-------|
| `test_device.py` | 49 | Device CRUD, claiming, assignments, control, deletion |
| `test_user.py` | 37 | Profile, role hierarchy, admin access, FCM tokens, cleanup |
| `test_stats.py` | 23 | Daily statistics, parameter validation, access control |
| `test_security.py` | 8 | JWT creation, verification, expiry, malformed tokens |

---

## Hardware Integration (ESP32)

### Publish sensor data

**Topic:** `devices/{MAC_ADDRESS}/data`

```json
{
  "temperature": 30.5,
  "humidity": 75.0,
  "ammonia": 12.5
}
```

All three fields are required. Validated ranges:

| Field | Min | Max | Unit |
|-------|----:|----:|------|
| `temperature` | -40 | 80 | °C |
| `humidity` | 0 | 100 | % |
| `ammonia` | 0 | 500 | ppm |

### Subscribe to control commands

**Topic:** `devices/{MAC_ADDRESS}/control`

```json
{
  "component": "kipas",
  "state": "ON"
}
```

Valid components: `kipas` · `lampu` · `pompa` · `pakan_otomatis`

---

## Author

**Bagus Ardiansyah** &mdash; Backend Engineer & System Architect

Built as part of Praktik Kerja Lapangan (PKL) 2026 at Palcomtech.

---

## License

This project was built for educational purposes (PKL).
