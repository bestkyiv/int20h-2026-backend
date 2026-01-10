from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"  # or "production"
    ALLOWED_ORIGINS: str = '["http://localhost:4321"]'

    DATABASE_URL: str = "sqlite+aiosqlite:///./backend.db"
