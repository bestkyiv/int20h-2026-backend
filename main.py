import logging
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import json
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings
from src.db.core import make_engine, make_session_factory, init_db
from src.api.form import router as form_router
from src.api.unis import router as unis_router
from src.api.categories import router as categories_router

logger = logging.getLogger(__name__)


def startup_db(engine):
    async def on_startup():
        logger.info("Initializing Database...")
        await init_db(engine)

    return on_startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
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
origins = json.loads(settings.ALLOWED_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(form_router)
app.include_router(unis_router)
app.include_router(categories_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
