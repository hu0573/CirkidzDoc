from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


def _ensure_sqlite_foreign_keys(dbapi_con, _con_record) -> None:
    """
    Enable SQLite foreign key constraints, which are disabled by default.
    """

    cursor = dbapi_con.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _resolve_database_url() -> str:
    if settings.database_url.startswith("sqlite:///"):
        sqlite_path = settings.database_url.split("sqlite:///")[1]
        db_path = Path(sqlite_path).expanduser()
        db_path.parent.mkdir(parents=True, exist_ok=True)

    return settings.database_url


engine: Engine = create_engine(
    _resolve_database_url(),
    echo=settings.database_echo,
    future=True,
)

if engine.url.get_backend_name() == "sqlite":
    event.listen(engine, "connect", _ensure_sqlite_foreign_keys)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_database() -> None:
    """
    Initialize the database schema (idempotent).
    """

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Session:
    """
    Provide a context-managed Session that automatically commits or rolls back.
    """

    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


