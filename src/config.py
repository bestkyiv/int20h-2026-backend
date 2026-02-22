from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"  # or "production"
    ALLOWED_ORIGINS: str = "http://localhost:4321"

    DATABASE_URL: str = "sqlite+aiosqlite:///./backend.db"
    REGISTRATION_END_DATE: str = "2026-02-22T23:59:59+02:00"
