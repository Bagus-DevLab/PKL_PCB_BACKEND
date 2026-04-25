# SESSION_HANDOFF.md

Handoff document for AI agents continuing work on this project.
Last updated: 2026-04-26 | Session: Staff Engineer Audit + Fixes

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
- **Auth:** Firebase Auth (login) → JWT (session) | 5-role RBAC hierarchy
- **Deploy:** GitHub Actions → SCP to VPS → Docker Compose

### Role Hierarchy
```
super_admin > admin > operator > viewer > user
```

---

## 2. What Was Accomplished This Session

### Staff Engineer Audit (9 findings, 5 fixed)

**Fixed:**

1. **Connection Pool Exhaustion (Critical)** — `app/database.py`
   - Default pool_size=5 caused blocking under WebSocket + HTTP load
   - Fix: `pool_size=3, max_overflow=7, pool_timeout=10, pool_recycle=1800`
   - Conditional: only applies for PostgreSQL (SQLite in tests skips these)

2. **JWT Auth Bypass for Deactivated Users (High)** — `app/routers/auth.py` + `app/routers/ws.py`
   - `firebase_login` issued JWT without checking `is_active`
   - `_authenticate_ws` returned user without checking `is_active`
   - Fix: Added `is_active` guard in both locations

3. **Missing Composite Index (High)** — `app/models/device.py`
   - `sensor_logs` queried by `(device_id, timestamp DESC)` without composite index
   - Fix: Added `Index("ix_sensor_logs_device_timestamp", "device_id", timestamp.desc())`
   - Migration: `005_add_composite_index_sensor_logs.py`

4. **TOCTOU Race in claim_device (Medium)** — `app/routers/device.py:78`
   - Two admins could claim same device simultaneously
   - Fix: Added `with_for_update()` for row-level locking

5. **SensorLog FK Missing CASCADE (Medium)** — `app/models/device.py:28`
   - `DELETE device` failed if MQTT worker inserted log during deletion
   - Fix: Added `ondelete="CASCADE"` to `SensorLog.device_id`
   - Migration: `004_add_cascade_to_sensor_log_device_fk.py`

**Not yet fixed (from audit):**

6. **Dashboard stats: 10 separate COUNT queries** — `app/routers/admin.py:37-56`
   - Should collapse to 2-3 queries using conditional aggregation
7. **N+1 query in get_device_assignments** — `app/routers/device.py:548-562`
   - Should use `joinedload(DeviceAssignment.user)`
8. **Unbounded DELETE in cleanup_logs** — `app/routers/admin.py:211-216`
   - Should delete in batches of 1000 to avoid WAL bloat
9. **MQTT worker queries device on every message** — `app/mqtt/mqtt_worker.py:101`
   - Should add in-memory MAC→device_id cache with 5-min TTL
10. **Notification cooldown not implemented** — documented in AGENTS.md but code missing
    - Should add 5-min per-device cooldown in mqtt_worker.py

### Earlier Work (Before Audit)

- **4-role → 5-role hierarchy:** super_admin, admin, operator, viewer, user
- **Device assignment system:** assign operator/viewer to specific devices
- **Admin dashboard:** React + shadcn/ui with charts, role management, device CRUD
- **Combined container:** Backend + Frontend in one Docker (Nginx + Uvicorn + Supervisor)
- **WebSocket streaming:** Real-time sensor data via `/api/ws/devices/{id}`
- **FCM push notifications:** Alert notifications to device owner + operators
- **Pagination:** All list endpoints return `{data, total, page, limit, total_pages}`
- **Data retention:** Cleanup endpoint + cron script for old sensor logs
- **CI/CD overhaul:** Migration runs before backend start, backup before deploy
- **Earthy color theme:** 5-color palette (#F1BF98, #E1F4CB, #BACBA9, #717568, #3F4739)
- **Landing page animations:** Framer Motion throughout (shimmer, float, stagger, hover)

---

## 3. Current Codebase State

| Metric | Value |
|--------|-------|
| Backend tests | **117 passed, 0 failed** |
| Frontend build | **Success** (code-split: 5 chunks) |
| Alembic head | `005_composite_index` |
| Local dev DB | Stamped at 005, all tables + indexes exist |
| Git status | Clean working tree, **15 commits ahead of origin/main** |
| VPS production | Running older version — needs `git push` + deploy |

### Migration Chain
```
001_add_role → 002_role_hierarchy → 003_fcm_tokens → 004_cascade_sensor_log → 005_composite_index
```

### Key Config
- `ENVIRONMENT=development` locally, `production` on VPS
- `INITIAL_ADMIN_EMAIL` → auto-promotes to `super_admin`
- `SENSOR_LOG_RETENTION_DAYS=365`
- `DEVICE_ONLINE_TIMEOUT_SECONDS=120`
- Pool: `pool_size=3, max_overflow=7` (PostgreSQL only)

---

## 4. Pending: Push to Production

**15 commits need to be pushed.** Before pushing:

1. Update `secrets.ENV_FILE` on GitHub if any new env vars were added
2. `git push origin main` → triggers GitHub Actions auto-deploy
3. On VPS after deploy: verify `alembic current` shows `005_composite_index`
4. Verify composite index exists: `SELECT indexname FROM pg_indexes WHERE tablename='sensor_logs'`

**Flutter app still needs `/api/` prefix update** — all API calls changed from `/devices/` to `/api/devices/` etc. Flutter users cannot access API until app is updated.

---

## 5. Next Steps / Phase 2: Resilience & Performance

### Priority 1: Remaining Audit Fixes
- [ ] Collapse dashboard stats to 2-3 queries (Finding 3)
- [ ] Fix N+1 in get_device_assignments with joinedload (Finding 4)
- [ ] Batch delete for cleanup_logs (Finding 6)
- [ ] MQTT device cache to reduce DB queries (Finding 7)
- [ ] Implement notification cooldown — 5 min per device (Finding 8)

### Priority 2: MQTT Worker Resilience
- [ ] Handle device deletion while MQTT worker is processing
- [ ] Add circuit breaker for FCM calls (prevent thread explosion)
- [ ] Monitor daemon thread count for notification threads

### Priority 3: WebSocket Edge Cases
- [ ] Periodic re-auth check (every 30s) for role changes / deactivation
- [ ] Graceful close when device is deleted
- [ ] Connection limit per user (prevent resource exhaustion)

### Priority 4: Production Hardening
- [ ] Add TLS to MQTT (port 8883)
- [ ] Reduce JWT expire time + implement refresh token
- [ ] Add integration tests with PostgreSQL (not just SQLite)

---

## 6. Key Files Reference

| File | Purpose |
|------|---------|
| `AGENTS.md` | Instructions for AI agents — **read this first** |
| `app/database.py` | Engine + pool config + SessionLocal |
| `app/dependencies.py` | Auth deps: get_current_user, get_device_with_access, etc. |
| `app/routers/device.py` | All device CRUD + assignment endpoints |
| `app/routers/ws.py` | WebSocket real-time streaming endpoint |
| `app/mqtt/mqtt_worker.py` | MQTT subscriber — sensor data ingestion |
| `app/mqtt/publisher.py` | MQTT publisher — device control commands |
| `app/core/notifications.py` | FCM push notification sender |
| `app/core/pagination.py` | Shared pagination helper with schema serialization |
| `app/core/ws_manager.py` | WebSocket connection manager singleton |
| `app/models/device.py` | Device, SensorLog, DeviceAssignment models |
| `app/models/user.py` | User, UserRole, FcmToken models |
| `tests/conftest.py` | Test fixtures — env vars set before imports |
