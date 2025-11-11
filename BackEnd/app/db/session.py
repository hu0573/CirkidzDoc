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
    SQLite 默认不开启外键，需要在连接时手动启用。
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
    初始化数据库（Idempotent）。
    """

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Session:
    """
    提供上下文管理的 Session，自动处理提交或回滚。
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


