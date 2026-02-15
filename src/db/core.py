from typing import AsyncGenerator
from fastapi import Request

from sqlmodel import SQLModel

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession



def make_engine(db_url: str) -> AsyncEngine:
    return create_async_engine(db_url, echo=False, future=True)


def make_session_factory(engine: AsyncEngine):
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine):
    """
    Creates tables.
    Note: 'models' must be imported before this runs!
    """
    async with engine.begin() as conn:
        # 3. Change Base.metadata -> SQLModel.metadata
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to provide an AsyncSession from app.state.session_factory."""
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        raise RuntimeError("Session factory is not initialized on app.state")

    async with session_factory() as session:
        yield session
