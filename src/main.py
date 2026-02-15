import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings
from src.db.core import make_engine, make_session_factory, init_db
from src.api.form import router as form_router
from src.api.unis import router as unis_router
from src.api.categories import router as categories_router
from src.api.skills import router as skills_router

from fastapi.exceptions import RequestValidationError
from src.logging_singleton import get_logger
from src.exceptions import CUSTOM_ERROR_MESSAGES

load_dotenv()

logger = get_logger(__name__)


def startup_db(engine):
    async def on_startup():
        logger.info("Initializing Database...")
        await init_db(engine)

    return on_startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    # create engine and session factory and expose on app.state
    engine = make_engine(settings.DATABASE_URL)
    session_factory = make_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory

    # initialize DB (create tables)
    await startup_db(engine)()

    try:
        yield
    finally:
        # dispose engine on shutdown
        try:
            await engine.dispose()
        except Exception:
            logger.exception("Error while disposing DB engine")


app = FastAPI(lifespan=lifespan)

settings = Settings()
origins = [
    origin.strip().rstrip("/")
    for origin in settings.ALLOWED_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
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
app.include_router(unis_router)
app.include_router(categories_router)
app.include_router(skills_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
