"""SQLAlchemy async engine and session factory for SQLite (aiosqlite)."""

import os
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


def _get_data_dir() -> Path:
    """Determine the data directory path.

    When running as a PyInstaller bundle (frozen), uses %APPDATA%/CM Report Server/data.
    Otherwise, uses server/data relative to the source tree.
    """
    if getattr(sys, "frozen", False):
        # 설치된 환경: %APPDATA%/CM Report Server/data
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        data_dir = Path(appdata) / "CM Report Server" / "data"
    else:
        # 개발 환경: server/data
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


DATA_DIR = _get_data_dir()
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR / 'cm_report.db'}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class for all ORM models."""

    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        yield session
