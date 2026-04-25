# Smart Chicken Box (PCB) Backend API

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-Mosquitto_2-3C5280?style=for-the-badge&logo=eclipse-mosquitto&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-Auth_+_FCM-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)
![Tests](https://img.shields.io/badge/Tests-117_Passed-2ea44f?style=for-the-badge)

A production-hardened IoT backend for monitoring and controlling smart chicken coops. Built with FastAPI, PostgreSQL, MQTT, and WebSockets — optimized for resource-constrained VPS deployments (2GB RAM, 2 cores).

This system powers real-time sensor telemetry from ESP32 microcontrollers, a 5-tier role-based access control hierarchy, push notification alerting, and a React admin dashboard — all served from a single Docker container behind Nginx.

---

## Architecture

```
  ESP32 Devices                       Flutter Mobile App
       |                                     |
       | MQTT (QoS 1)                        | HTTPS + WebSocket
       v                                     v
+-----------+    +----------------------------------------------------+
| Mosquitto |    |               VPS (Docker Compose)                  |
|   MQTT    |    |                                                     |
|  Broker   |<-->|  +----------------------------------------------+  |
|  :1883    |    |  |  pcb_pkl_backend (Supervisord)                |  |
+-----------+    |  |                                              |  |
       ^         |  |  Nginx :80                                   |  |
       |         |  |    /          -> React SPA (static)          |  |
       |         |  |    /admin/*   -> React Admin Dashboard       |  |
       |         |  |    /api/*     -> Uvicorn (FastAPI)           |  |
       |         |  |    /api/ws/*  -> WebSocket (upgrade)         |  |
       |         |  |                                              |  |
       |         |  |  Uvicorn :8000 (2 workers)                   |  |
       |         |  |    FastAPI Backend                           |  |
       |         |  +----------------------------------------------+  |
       |         |                                                     |
       |         |  +------------------+  +-------------------------+  |
       |         |  | pcb_pkl_postgres |  | pcb_pkl_mqtt_worker     |  |
       +---------|--| PostgreSQL 15    |  | Sensor data ingestion   |  |
                 |  | :5432            |  | Alert detection         |  |
                 |  +------------------+  | FCM push notifications  |  |
                 |                        +-------------------------+  |
                 +----------------------------------------------------+
```

**Data Flow:** ESP32 publishes sensor readings (temperature, humidity, ammonia) to Mosquitto via MQTT. The MQTT Worker subscribes, validates, and persists data to PostgreSQL while triggering FCM push notifications on threshold breaches. The Flutter app authenticates via Firebase, receives a local JWT, and streams real-time data over WebSockets. Admins control devices (fans, lights, pumps, feeders) through REST endpoints that publish MQTT commands back to the ESP32.

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
| **Rate Limiting** | slowapi (per-endpoint configurable) |
| **CI/CD** | GitHub Actions (auto-deploy to VPS) |
| **Testing** | pytest (117 test cases, SQLite in-memory) |

---

## Key Features

### Real-Time IoT Telemetry

- **Bi-directional MQTT** — ESP32 devices publish sensor data and subscribe to control commands via QoS 1.
- **WebSocket Streaming** — Live sensor data pushed to connected clients every 3 seconds with automatic device-deletion detection and anti-zombie connection cleanup.
- **Configurable Alert Thresholds** — Temperature and ammonia limits set via environment variables. Breaches trigger instant FCM push notifications.

### Advanced Role-Based Access Control (RBAC)

Five hierarchical roles with granular device-level permissions:

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

Device ownership is enforced at every layer — REST endpoints, WebSocket connections, and MQTT control commands all validate access through a unified dependency chain.

### Enterprise Resilience (Optimized for 2GB RAM)

| Optimization | Detail |
|-------------|--------|
| **Connection Pool Tuning** | `pool_size=3, max_overflow=7, pool_timeout=10s, pool_recycle=1800s` with `pool_pre_ping` for stale connection recovery. |
| **Batched Cleanup** | Sensor log retention deletes in batches of 1,000 rows to avoid long-running locks and WAL bloat. |
| **MQTT Device Cache** | In-memory MAC-to-device-ID cache with 5-minute TTL eliminates redundant DB lookups on every message. |
| **Graceful Shutdown** | SIGTERM handler cleanly disconnects the MQTT client and exits — no orphaned broker sessions. |
| **Bad Payload Rejection** | Strict topic validation (`devices/{mac}/data`), UTF-8 enforcement, JSON schema validation, and sensor range bounds. |
| **Anti-Zombie WebSockets** | Broken connections break the polling loop immediately. Device deletion/unclaim triggers proactive WebSocket closure via `ws_manager`. |
| **Dashboard Query Consolidation** | Admin stats use `GROUP BY` + conditional `CASE` aggregation — 3 queries instead of 10. |
| **N+1 Query Elimination** | Device assignments use `joinedload` for single-query eager loading. |
| **Non-Blocking Auth** | Auth dependencies are synchronous `def` (not `async def`), so FastAPI runs them in a threadpool instead of blocking the event loop. |

### Security Hardening

| Protection | Implementation |
|-----------|---------------|
| **Rate Limiting** | Every endpoint has a `slowapi` rate limit (5–60 req/min depending on sensitivity). |
| **Payload Size Limits** | Nginx `client_max_body_size 1m` + Pydantic `Field(max_length=...)` on all string inputs. |
| **JWT Active-State Validation** | Token verification checks `is_active` on every request — deactivated users are rejected immediately. |
| **Race Condition Protection** | `SELECT ... FOR UPDATE` on device claiming. `IntegrityError` catch-and-retry on first-login user creation. |
| **Notification Cooldown** | Max 1 FCM push per device per 5 minutes via `time.monotonic()` tracker — prevents alert spam. |
| **Error Sanitization** | Internal exception details are logged server-side but never returned to clients. Generic messages only. |
| **CORS Configuration** | Supports JSON array, comma-separated, and single-origin formats with explicit origin allowlist. |
| **Request ID Tracing** | Every request gets a unique ID via `X-Request-ID` header for end-to-end debugging. |

### Database Optimization

| Optimization | Detail |
|-------------|--------|
| **Composite B-Tree Index** | `ix_sensor_logs_device_timestamp` on `(device_id, timestamp DESC)` — optimizes the most frequent query pattern. |
| **CASCADE Foreign Keys** | `SensorLog.device_id` and `DeviceAssignment.device_id` use `ondelete="CASCADE"` for safe device deletion. |
| **5 Alembic Migrations** | `001_add_role` → `002_role_hierarchy` → `003_fcm_tokens` → `004_cascade_sensor_log` → `005_composite_index` |
---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2+
- [Python 3.12](https://www.python.org/downloads/) (for local development and testing)
- [Node.js 20+](https://nodejs.org/) (for frontend development)
- A [Firebase](https://console.firebase.google.com/) project with Authentication enabled
- `firebase-adminsdk.json` service account key file

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/pkl-pcb.git
cd pkl-pcb
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials. At minimum, set:

```env
SECRET_KEY=your_random_64_char_string_here
INITIAL_ADMIN_EMAIL=your-email@example.com
POSTGRES_PASSWORD=a_strong_database_password
```

Place your Firebase service account key at the project root:

```bash
cp /path/to/your/firebase-adminsdk.json ./firebase-adminsdk.json
```

### 3. Start All Services

```bash
# Development mode (auto-loads docker-compose.override.yml with hot-reload)
docker compose up -d --build

# Verify all containers are healthy
docker ps
```

### 4. Run Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Verify the Deployment

```bash
# Health check
curl http://localhost:8001/api/health
# Expected: {"status":"healthy","database_alive":true}

# API documentation (development mode only)
open http://localhost:8001/docs
```

### 6. Frontend Development (Optional)

```bash
cd pcb-landing-page
npm install
npm run dev
# Landing page:  http://localhost:5173/
# Admin login:   http://localhost:5173/admin/login
```

### Production Deployment

```bash
# Production mode (external volume protection, no hot-reload)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Run migrations
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | — | `development` or `production`. Controls API docs visibility and table auto-creation. |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string. Example: `postgresql://user:pass@postgres:5432/db` |
| `SECRET_KEY` | Yes | — | JWT signing key. Use a random string of 32+ characters. |
| `ALGORITHM` | No | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | — | JWT token lifetime in minutes. Recommended: `10080` (7 days). |
| `POSTGRES_USER` | Yes | — | PostgreSQL username (used by Docker Compose). |
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password (used by Docker Compose). |
| `POSTGRES_DB` | Yes | — | PostgreSQL database name (used by Docker Compose). |
| `MQTT_BROKER` | Yes | — | MQTT broker hostname. Use `mosquitto` for Docker network. |
| `MQTT_PORT` | No | `1883` | MQTT broker port. |
| `MQTT_TOPIC` | Yes | — | MQTT subscription pattern. Use `devices/+/data`. |
| `MQTT_USERNAME` | Yes | — | MQTT authentication username (can be empty for dev). |
| `MQTT_PASSWORD` | Yes | — | MQTT authentication password (can be empty for dev). |
| `CORS_ORIGINS` | Yes | — | Allowed origins. Supports JSON array, comma-separated, or single origin. |
| `INITIAL_ADMIN_EMAIL` | No | `""` | Email auto-promoted to `super_admin` on first login. |
| `ALERT_TEMP_MAX` | No | `35.0` | Temperature alert upper bound (Celsius). |
| `ALERT_TEMP_MIN` | No | `20.0` | Temperature alert lower bound (Celsius). |
| `ALERT_AMMONIA_MAX` | No | `20.0` | Ammonia alert upper bound (ppm). |
| `DEVICE_ONLINE_TIMEOUT_SECONDS` | No | `120` | Seconds since last heartbeat before device is considered offline. |
| `SENSOR_LOG_RETENTION_DAYS` | No | `365` | Days to retain sensor logs. Set `0` to disable cleanup. |
| `VITE_FIREBASE_*` | Yes | — | Firebase web config (6 variables). Passed as Docker build args for the React frontend. |

---

## Project Structure

```
pkl-pcb/
├── app/                              # FastAPI Backend
│   ├── core/                         # Framework utilities
│   │   ├── config.py                 #   Pydantic Settings (env validation)
│   │   ├── security.py               #   JWT creation & verification
│   │   ├── limiter.py                #   Shared slowapi rate limiter
│   │   ├── notifications.py          #   FCM push sender + cooldown logic
│   │   ├── pagination.py             #   Reusable query pagination helper
│   │   ├── ws_manager.py             #   WebSocket connection manager
│   │   ├── logging_config.py         #   Structured logging with request ID
│   │   └── request_context.py        #   ContextVar for request tracing
│   ├── models/                       # SQLAlchemy ORM models
│   │   ├── user.py                   #   User, UserRole (5-tier enum), FcmToken
│   │   └── device.py                 #   Device, SensorLog, DeviceAssignment
│   ├── routers/                      # API endpoint handlers
│   │   ├── auth.py                   #   POST /auth/firebase/login
│   │   ├── user.py                   #   /users/me CRUD, role management, FCM tokens
│   │   ├── device.py                 #   Device CRUD, logs, alerts, control, assignments
│   │   ├── admin.py                  #   Dashboard stats, user list, Firebase sync, cleanup
│   │   └── ws.py                     #   WebSocket real-time sensor streaming
│   ├── schemas/                      # Pydantic request/response schemas
│   │   ├── user.py                   #   UserResponse, UpdateUserRole, UpdateUserName
│   │   ├── device.py                 #   DeviceClaim, DeviceResponse, DailyStats
│   │   ├── sensor.py                 #   LogResponse
│   │   └── pagination.py             #   PaginatedResponse wrapper
│   ├── mqtt/                         # MQTT subsystem
│   │   ├── mqtt_worker.py            #   Subscriber: ingest, validate, alert, cache
│   │   └── publisher.py              #   Publisher: device control commands
│   ├── database.py                   # Engine, connection pool config, session factory
│   ├── dependencies.py               # Auth: get_current_user, role checks, device access
│   └── main.py                       # App init, lifespan, middleware, exception handlers
├── pcb-landing-page/                 # React Frontend (Landing Page + Admin Dashboard)
├── alembic/                          # Database migration scripts (5 migrations)
├── tests/                            # pytest test suite (117 test cases)
│   ├── conftest.py                   #   Fixtures, SQLite in-memory DB, test users
│   ├── test_device.py                #   49 tests: CRUD, claims, assignments, control
│   ├── test_security.py              #   8 tests: JWT creation, verification, expiry
│   ├── test_stats.py                 #   23 tests: daily statistics, validation, security
│   └── test_user.py                  #   37 tests: profile, roles, admin access, cleanup
├── scripts/                          # Operational scripts
│   ├── backup_db.sh                  #   PostgreSQL backup to .sql.gz
│   └── restore_db.sh                 #   Restore from backup
├── mosquitto/                        # Mosquitto broker configuration
├── Dockerfile                        # Multi-stage: Node build + Python + Nginx
├── docker-compose.yml                # Base: 4 services (backend, postgres, mosquitto, mqtt_worker)
├── docker-compose.override.yml       # Dev overrides (Uvicorn hot-reload, no Nginx)
├── docker-compose.prod.yml           # Prod overrides (external volumes, Supervisord)
├── nginx.conf                        # Nginx: SPA routing + API proxy + WebSocket upgrade
├── supervisord.conf                  # Process manager (Nginx + Uvicorn in one container)
├── requirements.txt                  # Python dependencies
├── alembic.ini                       # Alembic configuration
└── .github/workflows/deploy.yml      # CI/CD: auto-deploy on push to main
```

---

## Testing

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all 117 tests
pytest -v

# Run specific test modules
pytest tests/test_device.py -v
pytest tests/test_security.py -v
pytest tests/test_stats.py -v
pytest tests/test_user.py -v

# Run by pattern
pytest -k "test_admin_can" -v
```

| Module | Tests | Coverage |
|--------|-------|---------|
| `test_device.py` | 49 | Device CRUD, claiming, assignments, control, deletion |
| `test_security.py` | 8 | JWT creation, verification, expiry, malformed tokens |
| `test_stats.py` | 23 | Daily statistics, parameter validation, access control |
| `test_user.py` | 37 | Profile, role hierarchy, admin access, FCM tokens, cleanup |

---

## Hardware Integration (ESP32)

### Publish Sensor Data

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
|-------|-----|-----|------|
| `temperature` | -40 | 80 | Celsius |
| `humidity` | 0 | 100 | % |
| `ammonia` | 0 | 500 | ppm |

### Subscribe to Control Commands

**Topic:** `devices/{MAC_ADDRESS}/control`

```json
{
  "component": "kipas",
  "state": "ON"
}
```

Valid components: `kipas`, `lampu`, `pompa`, `pakan_otomatis`

---

## Author

**Bagus Ardiansyah** — Backend Engineer and System Architect

Built as part of Praktik Kerja Lapangan (PKL) 2026 at Palcomtech.

---

## License

This project was built for educational purposes (PKL).
