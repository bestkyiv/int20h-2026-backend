INT20H 2026 — Backend service

Overview

This repository implements a FastAPI backend for the INT20H 2026 event: registration form submission and reference APIs (skills, categories, universities). It exposes read endpoints and a single submission endpoint that validates and stores participant data in the database.

Key features

- REST API built with FastAPI + SQLModel/SQLAlchemy (async)
- Validation rules implemented with Pydantic models in `src/domain/models.py`
- Persistent storage using async SQLModel models (`src/db/models.py`)
- Lightweight endpoints for frontend consumption and server-side validation

---

Requirements

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) (recommended) **or** `pip`
- PostgreSQL 17 with the `pgvector` extension (production) — SQLite is used by default for local development and tests

---

Installation

**Using uv (recommended)**

```bash
uv sync
```

**Using pip**

```bash
pip install -r requirements.txt
```

For development tooling (linting, type checking, test extras):

```bash
# uv
uv sync --dev

# pip
pip install -e ".[dev]"
```

---

Configuration

Copy the example environment file and fill in the values:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./backend.db` | SQLAlchemy async connection string |
| `ALLOWED_ORIGINS` | `http://localhost:4321` | Comma-separated list of allowed CORS origins |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `REGISTRATION_END_DATE` | `2026-02-22T23:59:59+02:00` | ISO-8601 datetime after which submissions are rejected |

**PostgreSQL connection string format** (for production or local Postgres):

```
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname>
```

**Additional variables required by Docker Compose** (add to `.env`):

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=postgres
POSTGRES_PORT=5432
```

---

Local development (SQLite, no Docker)

SQLite is the default — no database setup is needed.

1. Install dependencies (see above).

2. Run database migrations:

```bash
alembic upgrade head
```

3. Seed reference data (categories, universities, skills):

```bash
python scripts/seed.py
```

4. Start the dev server:

```bash
uvicorn src.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

Local development with PostgreSQL (Docker Compose)

The `docker-compose.dev.yml` file starts a PostgreSQL 17 + pgvector instance, runs Alembic migrations, and seeds the database automatically.

```bash
# Start the database, run migrations, and seed data
docker compose -f docker-compose.dev.yml up -d

# Then start the backend locally
uvicorn src.main:app --reload
```

Services in `docker-compose.dev.yml`:

| Service | Description |
|---|---|
| `db` | PostgreSQL 17 with pgvector, persists data in a named volume |
| `migrator` | Runs `alembic upgrade head` once after `db` is healthy |
| `seeder` | Runs `docker/seed/seed.sql` once after migrations complete |

---

Database migrations (Alembic)

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration (autogenerate from model changes)
alembic revision --autogenerate -m "short description"

# Downgrade one step
alembic downgrade -1
```

Migration scripts live in `alembic/versions/`.

---

Project layout

```
src/
  main.py               — FastAPI app, middleware wiring, lifespan
  config.py             — Pydantic Settings (reads .env)
  api/                  — HTTP routers
    form.py             — POST /form/  (registration workflow)
    skills.py           — GET  /skills/
    categories.py       — GET  /categories/
    unis.py             — GET  /unis/
  db/
    core.py             — Engine / session factory helpers
    models.py           — SQLModel ORM models (Participant, Team, Category, University)
  domain/
    models.py           — Pydantic request/validation models (Form, cross-field validators)
  exceptions.py         — Custom exception types and error message overrides
  logging_singleton.py  — Shared logger instance
  middleware.py         — RegistrationDeadlineMiddleware

alembic/                — Alembic env and migration scripts
scripts/                — Seed and utility scripts
  seed.py               — Seeds categories, universities, and skills
  skills.json           — Static skill list served by GET /skills/
  unis.json             — University data used during seeding
docker/
  seed/seed.sql         — SQL seed file used by the Docker seeder service
tests/
  unit/                 — Fast isolated tests (no DB)
  api/                  — HTTP-level tests (override DB dependency with in-memory SQLite)
  integration/          — Full integration tests
```

---

API endpoints

### GET /skills/

Returns the static list of skill names from `scripts/skills.json`.

```json
["Python", "FastAPI", "React", ...]
```

### GET /categories/

```json
{ "categories": [{"id": 1, "name": "..."}, ...] }
```

### GET /unis/

```json
{ "universities": [{"id": 1, "name": "...", "city": "..."}, ...] }
```

### POST /form/

Submits a participant registration. Key request fields:

| Field | Type | Notes |
|---|---|---|
| `full_name` | `str` | |
| `email` | `str` | Unique — duplicate rejected with 400 |
| `telegram` | `str` | Unique — duplicate rejected with 400 |
| `phone` | `str` | E.164 format |
| `is_student` | `bool` | |
| `university_id` | `int \| null` | Must exist in the DB |
| `study_year` | enum | |
| `category_id` | `int` | Must exist in the DB |
| `skills` | `list[str]` | |
| `format` | `"online" \| "offline"` | |
| `has_team` | `bool` | |
| `team_leader` | `bool` | |
| `team_name` | `str` | |
| `wants_job` | `bool` | |
| `cv` | URL | |
| `linkedin` | URL | |
| `work_consent` | `bool` | |
| `personal_data_consent` | `bool` | Must be `true` |

Business rules (see `src/domain/models.py` and `src/api/form.py` for full detail):

- Cross-field constraints validated via `model_validator`.
- Duplicate email or telegram → 400.
- `has_team=true` + `team_leader=true` → creates a new team and assigns the participant as leader.
- `has_team=true`, team already exists → participant joins it (category must match).

**Success:** `200 {"message": "...", "data": <submitted payload>}`  
**Validation error:** `422 {"detail": "<message>"}`  
**Business error:** `400 {"detail": "<message>"}`

---

Testing

```bash
# Run all tests
pytest -q

# Run only fast unit tests
pytest -q -m unit

# Run with coverage report
pytest --cov=src --cov-report=html
```

Tests use an in-memory SQLite database and override the DB dependency — no external services required.

Available markers: `unit`, `integration`, `slow`, `db`, `api`.

---

Linting and formatting

```bash
# Check
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Format
ruff format .
```

---

Production (Docker)

```bash
# Build and run
docker build -t int-backend .
docker run --env-file .env -p 8000:8000 int-backend
```

The container entrypoint (`start.sh`) runs migrations, seeds the database, then starts Uvicorn.
