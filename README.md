INT20H 2026 — Backend service

Overview

This repository implements a small FastAPI backend for the INT20H 2026 event registration form and reference APIs (skills, categories, universities). It exposes a few read endpoints and a single submission endpoint that validates and stores participant data in the database.

Key features

- REST API built with FastAPI + SQLModel/SQLAlchemy (async)
- Validation rules implemented with Pydantic models in `src/domain/models.py`
- Persistent storage using async SQLModel models (`src/db/models.py`)
- Lightweight endpoints for frontend consumption and server-side validation

Quick start

Requirements

- Python 3.13+
- Install dependencies: pip install -r requirements.txt

Run the app locally

- Using Uvicorn:

```bash
uvicorn src.main:app --reload
```

- Default HTTP port: 8000

API endpoints (summary)

1. GET /skills/

- Purpose: return static list of skill names (served from `scripts/skills.json`).
- Response: JSON array of strings.
- Example: ["Python", "FastAPI", ...]

2. GET /categories/

- Purpose: list available competition categories.
- Response: { "categories": [ {"id": 1, "name": "..."}, ... ] }
- Source: `src/db/models.py::Category`

3. GET /unis/

- Purpose: list supported universities.
- Response: { "universities": [ {"id": 1, "name": "...", "city": "..."}, ... ] }
- Source: `src/db/models.py::University`

4. POST /form/

- Purpose: submit registration form for a participant.
- Request body: `src/domain/models.py::Form` (Pydantic model). Important fields:
  - full_name (str)
  - email (str)
  - telegram (str)
  - phone (E.164 format validated)
  - is_student (bool)
  - university_id (int | null)
  - study_year (enum)
  - category_id (int)
  - skills (list[str])
  - format ("online" | "offline")
  - has_team (bool), team_leader (bool), team_name (str)
  - wants_job (bool), cv (url), linkedin (url), work_consent (bool)
  - personal_data_consent (must be true)

- Behavior / business rules (high-level):
  - Validates field-level and cross-field constraints (see `Form.model_validator`).
  - Rejects duplicate registrations (same email or telegram).
  - Validates `university_id` and `category_id` existence.
  - If `has_team` and `team_leader` true → creates team + assigns participant as leader.
  - If `has_team` and team exists → participant joins existing team (category must match).

- Success response: 200 with {"message": "...", "data": <submitted payload>}
- Error responses: 400 for business/validation errors, 422 for Pydantic validation errors.

Database models (brief)

- Participant — stores submitted registrations (personal, university, category, team link, CV/linkedin, skills_text).
- Team — team_name + category_id; unique constraint on (team_name, category_id).
- Category — competition categories (id, name).
- University — universities (id, name, city).

Project layout

- src/
  - main.py — FastAPI app and startup/lifespan
  - api/ — HTTP routers (`form.py`, `skills.py`, `categories.py`, `unis.py`)
  - db/ — SQLModel DB models + core session helpers
  - domain/ — Pydantic request/validation models
  - logging_singleton.py, config.py, exceptions.py — infra
- scripts/ — supporting files (e.g. `skills.json`)

Testing

- Tests are located in `tests/` (pytest + pytest-asyncio).
- Run all tests:

```bash
pytest -q
```

- The test suite uses an in-memory SQLite DB and overrides the DB dependency for API tests.

Adding endpoints / Contributing

- Add new API endpoints under `src/api/` and write input validation in `src/domain/`.
- Add DB tables under `src/db/models.py` and create Alembic migrations if necessary.
- Add unit tests under `tests/unit/` and API/integration tests under `tests/api/` or `tests/integration/`.

Contact

- For design/behaviour questions, inspect `src/domain/models.py` (validation) and `src/api/form.py` (registration workflow).
