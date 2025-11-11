from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TaskStatusEnum(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TemplateRecord(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry: Mapped[str] = mapped_column(String(255))
    config_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tasks: Mapped[list["TaskRecord"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class TaskRecord(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    template_id: Mapped[str] = mapped_column(ForeignKey("templates.id", ondelete="CASCADE"))
    status: Mapped[TaskStatusEnum] = mapped_column(default=TaskStatusEnum.QUEUED)
    requested_formats: Mapped[list[str]] = mapped_column(JSON, default=list)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    requested_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    template: Mapped[TemplateRecord] = relationship(back_populates="tasks")
    results: Mapped[list["TaskResultRecord"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class TaskResultRecord(Base):
    __tablename__ = "task_results"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    format: Mapped[str] = mapped_column(String(32))
    file_name: Mapped[str] = mapped_column(String(255))
    relative_path: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    download_token: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    task: Mapped[TaskRecord] = relationship(back_populates="results")


