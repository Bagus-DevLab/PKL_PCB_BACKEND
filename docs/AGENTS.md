# AGENTS.md

Instructions for AI agents working in this repository.

## Architecture

Monorepo: FastAPI backend + React frontend served from **one Docker container** via Nginx (static files) + Uvicorn (API) managed by Supervisord.

```
app/                  → FastAPI backend (Python 3.11)
pcb-landing-page/     → React 19 frontend (Vite 7, Tailwind v4, shadcn/ui)
```

All API endpoints are prefixed with `/api`. The frontend calls `/api/*` which Nginx proxies to Uvicorn. Do not create endpoints without the `/api` prefix — they will conflict with React SPA routing.

## Development Commands

```bash
# Backend (Docker)
docker compose up -d                    # dev mode (auto-loads override)
docker compose exec backend alembic upgrade head  # run migrations

# Frontend (separate terminal)
cd pcb-landing-page && npm run dev      # Vite dev server on :5173

# Tests
source .venv/bin/activate && pytest     # 117 test cases, SQLite in-memory
pytest tests/test_device.py -v          # single file
pytest -k "test_admin_can"              # pattern match

# Production deploy (no override)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Testing Quirks

- Tests use **SQLite in-memory**, production uses **PostgreSQL**. Behavior differences exist (e.g., `func.date()`, UUID handling).
- `tests/conftest.py` sets `os.environ` variables **before** importing any app modules. If you add a new required config variable to `Settings`, you must also add it to conftest.py or tests will crash.
- `test_device_claimed` fixture belongs to `test_admin_user` (role: admin), not `test_user` (role: user). Use `admin_headers` for device access tests.
- Paginated endpoints return `{"data": [...], "total": N, "page": 1, "limit": 20, "total_pages": N}`, not plain arrays. Tests must extract `response.json()["data"]`.

## Database & Migrations

- Alembic `sqlalchemy.url` in `alembic.ini` is a placeholder — overridden by `alembic/env.py` which reads from `app.core.config.settings`.
- `Base.metadata.create_all()` runs only in development (`ENVIRONMENT != "production"`). Production relies on Alembic.
- If migration fails with "table already exists", use `alembic stamp head` to mark it as applied.
- When adding new models, import them in `alembic/env.py` so autogenerate detects them.

## Role System (5 roles, hierarchical)

```
super_admin > admin > operator > viewer > user
```

- `super_admin`: full system access, register devices, manage all roles
- `admin`: claim devices, assign operator/viewer to own devices
- `operator`: view + control assigned devices
- `viewer`: view-only on assigned devices
- `user`: default on registration, no device access

Access control is in `app/dependencies.py`: `get_current_user`, `get_current_admin` (super_admin + admin), `get_current_super_admin`, `get_device_with_access`, `check_can_control_device`, `get_owned_device`.

## Environment Variables

- `app/core/config.py` uses `extra = "ignore"` — unknown env vars (like `VITE_FIREBASE_*`) are silently ignored by Pydantic Settings.
- `CORS_ORIGINS` accepts three formats: JSON array, comma-separated, or single origin. The `parse_cors_origins` validator handles all three.
- `VITE_FIREBASE_*` variables are passed as Docker **build args** (not runtime env). They're baked into the React build at image creation time.
- `INITIAL_ADMIN_EMAIL` auto-promotes the matching user to `super_admin` on startup.

## Docker

- **Dev mode**: `docker compose up -d` loads `docker-compose.override.yml` automatically. Uvicorn listens on port 80 (not 8000) to match the production port mapping `8001:80`.
- **Production**: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`. Uses Supervisord (Nginx + Uvicorn). Volume `api-pcb_postgres_data` is marked `external: true` for protection.
- The `pcb-landing-page/` directory has no Dockerfile — it's built in stage 1 of the root `Dockerfile`.

## CI/CD (GitHub Actions)

Deploy triggers on push to `main`. Key sequence:
1. SCP files to VPS `/opt/api-pcb`
2. Inject `.env` from `secrets.ENV_FILE`
3. Backup database
4. Build Docker images
5. Start postgres + mosquitto
6. **Run Alembic migration** (before backend starts)
7. Start backend + mqtt_worker
8. Health check

Migration runs via temporary container connected to the Docker network, not via `docker exec` on the running backend.

## Frontend

- Path alias `@` maps to `src/` (configured in `vite.config.js` and `jsconfig.json`).
- API client is in `src/lib/api.js`. All error handling uses `getErrorMessage()` helper which handles both string and array (validation) error formats from FastAPI.
- Admin dashboard accessible at `/admin/*`. Auth check accepts both `super_admin` and `admin` roles.
- `useAuth` hook in `src/admin/hooks/useAuth.js` verifies token against backend on page load (not just localStorage).
- `useDeviceStream` hook in `src/admin/hooks/useDeviceStream.js` connects to WebSocket at `/api/ws/devices/{id}?token=JWT`.

## MQTT

- `paho-mqtt==2.1.0` (v2 API). Callbacks use `CallbackAPIVersion.VERSION2` signature: `on_connect(client, userdata, flags, reason_code, properties)`.
- Publisher (`app/mqtt/publisher.py`) uses thread-safe singleton with `threading.Lock`.
- Worker (`app/mqtt/mqtt_worker.py`) runs as separate container. Alert notifications are sent in daemon threads to avoid blocking message processing.
- Notification cooldown: max 1 push notification per device per 5 minutes (in-memory tracker in `notifications.py`).

## Common Pitfalls

- **Adding env vars**: Add to `config.py`, `.env.example`, `tests/conftest.py`, and `secrets.ENV_FILE` on GitHub.
- **New models**: Import in `alembic/env.py` and `app/models/__init__.py`.
- **Paginated endpoints**: Use `paginate(query, page, limit, schema=YourSchema)` — always pass `schema` to avoid exposing raw ORM fields.
- **Device access**: Never query `Device.user_id == current_user.id` directly. Use `get_device_with_access()` or `get_owned_device()` which handle all 5 roles.
- **WebSocket auth**: Uses query parameter `?token=JWT` (not headers). The `_authenticate_ws` function must mirror checks from `get_current_user` including `is_active`.
- **CORS in production**: Use comma-separated format (`CORS_ORIGINS=https://a.com,https://b.com`). JSON array format can break when GitHub Actions writes `.env`.
