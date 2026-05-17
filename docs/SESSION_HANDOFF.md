# SESSION_HANDOFF.md

Handoff document for AI agents continuing work on this project.
Last updated: 2026-05-17 | Session: Documentation consistency pass

---

## 1. Project Overview

**PKL PCB Smart Kandang** — IoT platform for monitoring chicken coops.

### Architecture
```
VPS (2GB RAM, 2 Cores)
├── pcb_pkl_backend (Docker)
│   ├── Nginx (:80) → React static + proxy /api/ to Uvicorn
│   └── Uvicorn (:8000, 2 workers) → FastAPI
├── pcb_pkl_mqtt_worker (Docker) → paho-mqtt v2, writes sensor data
├── pcb_pkl_postgres (Docker) → PostgreSQL 15
└── pcb_pkl_mosquitto (Docker) → Eclipse Mosquitto 2 (MQTT broker)
```

### Tech Stack
- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic, PyJWT, paho-mqtt 2.1
- **Frontend:** React 19, Vite 7, Tailwind v4, shadcn/ui, Recharts, Framer Motion
- **Auth:** Firebase Auth (login) → local JWT (session) | 5-role RBAC hierarchy
- **Deploy:** GitHub Actions → SCP to VPS → Docker Compose

### Role Hierarchy
```
super_admin > admin > operator > viewer > user
```

---

## 2. Current Codebase State

| Metric | Value |
|--------|-------|
| Backend tests | **117 collected** via `pytest --collect-only -q` |
| Docker Python runtime | **Python 3.11** (`python:3.11-slim`) |
| Local test Python observed | **Python 3.12.3** |
| Frontend | React 19 + Vite 7 |
| Alembic head | `006_light_level` |
| Migration chain | `001_add_role` → `002_role_hierarchy` → `003_fcm_tokens` → `004_cascade_sensor_log` → `005_composite_index` → `006_light_level` |
| API prefix | All REST and WebSocket routes are served under `/api` |

### Implemented Resilience/Performance Fixes

- PostgreSQL connection pool tuned in `app/database.py`: `pool_size=3`, `max_overflow=7`, `pool_timeout=10`, `pool_recycle=1800`, `pool_pre_ping`.
- Deactivated users are rejected on Firebase login and WebSocket auth.
- `sensor_logs` has `(device_id, timestamp DESC)` composite index.
- Device claiming uses `SELECT ... FOR UPDATE` to prevent concurrent claim races.
- `SensorLog.device_id` and `DeviceAssignment.device_id` use cascade deletion behavior.
- Dashboard stats are consolidated into role/device aggregate queries.
- Device assignment listing uses `joinedload(DeviceAssignment.user)`.
- Sensor-log cleanup deletes in batches of 1000 rows.
- MQTT worker has a 5-minute in-memory MAC-to-device cache.
- FCM alert notifications have a 5-minute per-device cooldown.
- WebSockets close proactively when a device is deleted or unclaimed.

### Current Hardware/API State

- Sensor payload required fields: `temperature`, `humidity`, `ammonia`.
- `light_level` is supported but optional/backward-compatible; omitted or invalid values are stored as `null`.
- Valid control components: `kipas`, `lampu`, `pompa`, `pakan_otomatis`, `exhaust_fan`.
- Device registration (`POST /api/devices/register`) is `super_admin` only.
- Device claiming (`POST /api/devices/claim`) is available to `super_admin` and `admin`.

---

## 3. Key Config

- `ENVIRONMENT=development` locally, `production` on VPS.
- `INITIAL_ADMIN_EMAIL` auto-promotes the matching user to `super_admin`.
- `SENSOR_LOG_RETENTION_DAYS=365` by default; `0` disables cleanup.
- `DEVICE_ONLINE_TIMEOUT_SECONDS=120`.
- `VITE_FIREBASE_*` values are Docker build args for the React build, not runtime-only backend env vars.
- `CORS_ORIGINS` accepts JSON array, comma-separated list, or a single origin.

---

## 4. Operational Notes

- Production relies on Alembic migrations; `Base.metadata.create_all()` only runs outside production.
- Run `alembic upgrade head` after deploy and verify production reaches `006_light_level`.
- Git/VPS deployment status is intentionally not tracked here because it becomes stale quickly. Use `git status`, `git log @{u}..`, and the GitHub Actions run history for current deployment state.
- MQTT credentials and broker host should come from `.env` / deployment secrets. Do not hardcode real broker credentials in docs or firmware committed to the repo.

---

## 5. Next Steps

### Priority 1: Production Hardening
- [ ] Add TLS for MQTT (port 8883).
- [ ] Rotate any MQTT credentials that were ever committed or shared in documentation.
- [ ] Reduce JWT lifetime and add refresh-token flow if the mobile app needs longer sessions.
- [ ] Add PostgreSQL integration tests for behavior that SQLite cannot faithfully cover.

### Priority 2: MQTT Worker Resilience
- [ ] Add a circuit breaker or bounded worker pool for FCM calls to avoid unbounded notification threads.
- [ ] Monitor notification thread count and FCM failure rate.
- [ ] Invalidate MQTT device cache more actively on device delete/unclaim if real-time consistency becomes necessary.

### Priority 3: WebSocket Edge Cases
- [ ] Periodic re-auth check for role changes and user deactivation during long-lived connections.
- [ ] Per-user or per-device WebSocket connection limits.

---

## 6. Key Files Reference

| File | Purpose |
|------|---------|
| `docs/AGENTS.md` | Instructions for AI agents — read this first |
| `docs/API_CONTRACT.md` | REST/WebSocket contract for Flutter/mobile clients |
| `docs/HARDWARE_INTEGRATION.md` | ESP32/MQTT/BLE integration guide |
| `app/database.py` | Engine + pool config + SessionLocal |
| `app/dependencies.py` | Auth deps: get_current_user, role checks, device access |
| `app/routers/device.py` | Device CRUD, logs, alerts, control, assignments |
| `app/routers/ws.py` | WebSocket real-time streaming endpoint |
| `app/mqtt/mqtt_worker.py` | MQTT subscriber — sensor data ingestion |
| `app/mqtt/publisher.py` | MQTT publisher — device control commands |
| `app/core/notifications.py` | FCM push sender + cooldown |
| `app/core/pagination.py` | Shared pagination helper |
| `app/core/ws_manager.py` | WebSocket connection manager singleton |
| `app/models/device.py` | Device, SensorLog, DeviceAssignment models |
| `app/models/user.py` | User, UserRole, FcmToken models |
| `tests/conftest.py` | Test fixtures and required env vars before imports |
