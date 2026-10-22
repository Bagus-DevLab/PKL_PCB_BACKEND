# Repository Guidelines

## Project Structure

This repository combines a FastAPI IoT backend and a React admin/landing frontend. Backend code lives in `app/`: routes in `routers/`, database models in `models/`, request schemas in `schemas/`, shared services in `core/`, and MQTT integration in `mqtt/`. The Vite frontend is under `pcb-landing-page/src/`; reusable UI and page components are grouped in `components/` and `admin/`. Pytest tests are in `tests/`, Alembic migrations in `alembic/versions/`, operational scripts in `scripts/`, and project documentation in `docs/`.

## Build, Test, and Development

- `docker compose up -d --build` starts the development stack; Compose loads `docker-compose.override.yml` automatically.
- `docker compose exec backend alembic upgrade head` applies database migrations.
- `pytest` runs the backend suite (configured by `pytest.ini`; most tests use in-memory SQLite). Run a focused file with `pytest tests/test_device.py`.
- PostgreSQL integration tests use the `postgres` marker; configure the test database as described in `docker-compose.test.yml` and run `pytest -m postgres`.
- `cd pcb-landing-page && npm install && npm run dev` starts Vite. Use `npm run build` for a production build and `npm run lint` for ESLint.

## Style and Naming

Follow the surrounding code. Python uses four-space indentation, `snake_case` modules/functions, and `PascalCase` classes. Tests follow `test_*.py` filenames and `test_*` function names. React uses `.jsx` modules, `PascalCase` component names, and `use*` hook names; use the `@/` alias for frontend imports from `src/`. ESLint is the frontend lint check; no Python formatter is configured in the repository.

## Testing Guidelines

Add or update tests with behavior changes. Keep API tests near related coverage in `tests/`, use shared fixtures from `tests/conftest.py`, and mark tests requiring PostgreSQL with `@pytest.mark.postgres`. Cover authorization and validation paths when changing API behavior.

## Commits and Pull Requests

Recent history uses short conventional subjects such as `feat: ...`, `test: ...`, `docs: ...`, and `chore: ...`; keep the subject imperative and focused. Pull requests should explain the change and its impact, link related issues when available, list relevant test/build commands and results, and include screenshots for visible frontend changes.

## Configuration and Secrets

Start from `.env.example` and keep credentials out of source control. When adding a required setting, update `app/core/config.py`, `.env.example`, and the test environment in `tests/conftest.py` together. Use Alembic migrations for schema changes.
