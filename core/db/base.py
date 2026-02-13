from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for persistent models."""


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/open_epistemic")


def create_engine_sync():
    return create_engine(get_database_url(), future=True)


def get_session_factory() -> sessionmaker[Session]:
    engine = create_engine_sync()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency helper for DB sessions (not yet wired)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()

