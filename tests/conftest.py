import pytest_asyncio
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import event
from httpx import AsyncClient
from fastapi import FastAPI
from src.api.form import router as form_router
from src.api.skills import router as skills_router
from src.api.categories import router as categories_router
from src.api.unis import router as unis_router
from src.db import models as db_models
from src.db.core import get_session as get_session_dep


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def session(async_session_factory):
    async with async_session_factory() as sess:
        yield sess


@pytest_asyncio.fixture
async def test_app(async_session_factory):
    """Creates a FastAPI test app that overrides DB dependency to use the test session factory."""
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    from src.exceptions import CUSTOM_ERROR_MESSAGES
    from src.logging_singleton import get_logger

    logger = get_logger(__name__)

    app = FastAPI()

    # Register custom exception handler for validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """
        Handles Pydantic validation errors.
        1. Checks for custom messages in CUSTOM_ERROR_MESSAGES.
        2. Removes 'Value error, ' prefix from custom validators.
        """
        if not exc.errors():
            return JSONResponse(status_code=422, content={"detail": "Validation error"})

        # Grab the first error
        error = exc.errors()[0]

        # Extract metadata
        # 'loc' is a tuple like ('body', 'job_description'). We want the last part.
        field_name = str(error["loc"][-1]) if error["loc"] else "unknown"
        error_type = error["type"]  # e.g., 'string_too_long', 'value_error', 'missing'
        raw_msg = error["msg"]

        # Step 1: Check if we have a custom override for this specific field and error type
        custom_msg = None
        if field_name in CUSTOM_ERROR_MESSAGES:
            custom_msg = CUSTOM_ERROR_MESSAGES[field_name].get(error_type)

        # Step 2: If no custom message, clean up the default Pydantic message
        if not custom_msg:
            if raw_msg.startswith("Value error, "):
                custom_msg = raw_msg.replace("Value error, ", "")
            elif raw_msg.startswith("Assertion failed, "):
                custom_msg = raw_msg.replace("Assertion failed, ", "")
            else:
                # Fallback to default (e.g., "Field required")
                custom_msg = raw_msg

        logger.warning(f"Validation error on field '{field_name}': {custom_msg}")

        # Return the simple structure you requested
        return JSONResponse(status_code=422, content={"detail": custom_msg})

    app.include_router(form_router)
    app.include_router(skills_router)
    app.include_router(categories_router)
    app.include_router(unis_router)

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session_dep] = _override_get_session
    return app


@pytest_asyncio.fixture
async def client(test_app):
    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
def category_factory(session):
    async def _create_category(name: str = "Test Category"):
        category = db_models.Category(name=name)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    return _create_category


@pytest_asyncio.fixture
def university_factory(session):
    async def _create_university(name: str = "Test Uni", city: str | None = None):
        uni = db_models.University(name=name, city=city)
        session.add(uni)
        await session.commit()
        await session.refresh(uni)
        return uni

    return _create_university


@pytest_asyncio.fixture
def team_factory(session):
    async def _create_team(category_id: int, team_name: str = "Team X"):
        team = db_models.Team(team_name=team_name, category_id=category_id)
        session.add(team)
        await session.commit()
        await session.refresh(team)
        return team

    return _create_team
