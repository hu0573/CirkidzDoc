from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import TaskRecord, TaskResultRecord, TaskStatusEnum, TemplateRecord
from app.db.session import session_scope
from app.models.templates import RenderRequest, RenderResponse, TaskResult, TaskStatus, TemplateMetadata
from app.services.render_engine import RenderEngine, RenderOutcome, render_engine
from app.services.templates import TemplateRepository, template_repository


class TaskNotFoundError(KeyError):
    pass


class TaskService:
    """
    Service that encapsulates task creation, status retrieval, and result management operations.
    """

    def __init__(
        self,
        *,
        repository: TemplateRepository = template_repository,
        engine: RenderEngine = render_engine,
        results_root: Path | None = None,
    ) -> None:
        self.repository = repository
        self.engine = engine
        self.results_root = results_root or settings.results_root

    # ------------------------ Template Sync --------------------- #
    @staticmethod
    def _upsert_template(session: Session, metadata: TemplateMetadata) -> None:
        record = session.get(TemplateRecord, metadata.id)
        if record is None:
            record = TemplateRecord(
                id=metadata.id,
                name=metadata.name,
                description=metadata.description,
                version=metadata.version,
                entry=metadata.entry,
                status="active",
            )
            session.add(record)
        else:
            record.name = metadata.name
            record.description = metadata.description
            record.version = metadata.version
            record.entry = metadata.entry

    # ------------------------ Clean up --------------------- #
    def cleanup_expired_tasks(self) -> int:
        """
        Delete expired tasks and their associated files.
        """

        now = datetime.now(timezone.utc)
        removed = 0

        with session_scope() as session:
            stmt = select(TaskRecord).where(TaskRecord.expires_at < now)
            expired_tasks = session.scalars(stmt).all()

            for task in expired_tasks:
                results_dir = self._task_results_dir(task.id)
                if results_dir.exists():
                    shutil.rmtree(results_dir, ignore_errors=True)

            if expired_tasks:
                task_ids = [task.id for task in expired_tasks]
                session.execute(delete(TaskRecord).where(TaskRecord.id.in_(task_ids)))
                removed = len(task_ids)
                logger.info("Removed {count} expired tasks", count=removed)

        return removed

    # ------------------------ Task lifecycle --------------------- #
    @staticmethod
    def _normalise_formats(request: RenderRequest, metadata: TemplateMetadata) -> list[str]:
        if request.formats:
            return [fmt.lower() for fmt in dict.fromkeys(request.formats)]

        if metadata.options and metadata.options.allowed_outputs:
            return [fmt.lower() for fmt in metadata.options.allowed_outputs]

        if metadata.entry.lower().endswith(".docx"):
            return ["docx"]

        if metadata.entry.lower().endswith(".pdf"):
            return ["pdf"]

        return ["docx"]

    def create_task(self, request: RenderRequest) -> RenderResponse:
        metadata = self.repository.get_template(request.template_id)
        formats = self._normalise_formats(request, metadata)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.task_expiry_minutes)
        task_id = uuid4().hex

        # Clean up expired data before creating a new async task to prevent disk growth.
        self.cleanup_expired_tasks()

        with session_scope() as session:
            self._upsert_template(session, metadata)

            task = TaskRecord(
                id=task_id,
                template_id=metadata.id,
                status=TaskStatusEnum.QUEUED,
                requested_formats=formats,
                options=request.options,
                payload={
                    "data": request.data,
                    "formats": formats,
                    "options": request.options,
                },
                expires_at=expires_at,
            )
            session.add(task)

        return RenderResponse(task_id=task_id, status="queued", expires_at=expires_at)

    def get_task(self, task_id: str) -> TaskRecord:
        with session_scope() as session:
            task = session.get(TaskRecord, task_id)
            if task is None:
                raise TaskNotFoundError(task_id)
            # detach
            session.expunge(task)
            for result in task.results:
                session.expunge(result)
            return task

    # ------------------------ Status building --------------------- #
    def _convert_results(self, results: Iterable[TaskResultRecord]) -> list[TaskResult]:
        converted: list[TaskResult] = []
        for result in results:
            download_url = f"/api/templates/tasks/{result.task_id}/files/{result.format}?token={result.download_token}"
            converted.append(
                TaskResult(
                    format=result.format,
                    download_url=download_url,
                    file_size=result.file_size,
                    checksum=result.checksum,
                    expires_at=result.expires_at,
                )
            )
        return converted

    def build_status(self, task: TaskRecord) -> TaskStatus:
        return TaskStatus(
            task_id=task.id,
            status=task.status.value,
            progress=task.progress,
            error=task.error_message,
            results=self._convert_results(task.results),
        )

    # ------------------------ Execution --------------------- #
    def _task_results_dir(self, task_id: str) -> Path:
        path = self.results_root / task_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _archive_outcome(self, task: TaskRecord, outcome: RenderOutcome) -> TaskResultRecord:
        target_dir = self._task_results_dir(task.id)
        extension = outcome.file_path.suffix or f".{outcome.format}"
        file_name = f"{task.id}{extension}"
        target_path = target_dir / file_name
        shutil.copy2(outcome.file_path, target_path)

        file_size = target_path.stat().st_size
        checksum = self._compute_checksum(target_path)
        token = uuid4().hex
        expires_at = task.expires_at

        try:
            outcome.file_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            logger.warning("Failed to delete temporary file: {path}", path=outcome.file_path.as_posix())

        return TaskResultRecord(
            id=uuid4().hex,
            task_id=task.id,
            format=outcome.format,
            file_name=file_name,
            relative_path=target_path.relative_to(self.results_root).as_posix(),
            file_size=file_size,
            checksum=checksum,
            download_token=token,
            expires_at=expires_at,
        )

    @staticmethod
    def _compute_checksum(path: Path) -> str:
        import hashlib

        hasher = hashlib.sha256()
        with path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def process_task(self, task_id: str) -> None:
        logger.info("Starting to process task {task_id}", task_id=task_id)
        with session_scope() as session:
            task = session.get(TaskRecord, task_id)
            if task is None:
                logger.error("Task {task_id} does not exist. Skipping execution.", task_id=task_id)
                return

            try:
                task.status = TaskStatusEnum.PROCESSING
                task.progress = 10
                session.flush()

                request_payload = task.payload
                render_request = RenderRequest(
                    template_id=task.template_id,
                    data=request_payload.get("data", {}),
                    formats=request_payload.get("formats", task.requested_formats),
                    options=request_payload.get("options"),
                )

                outcomes = self.engine.render(render_request)
                sanitized_outcomes = [self._archive_outcome(task, outcome) for outcome in outcomes]

                task.results.clear()
                task.results.extend(sanitized_outcomes)
                task.status = TaskStatusEnum.SUCCEEDED
                task.progress = 100

                logger.info("Task {task_id} finished with {count} generated results", task_id=task_id, count=len(outcomes))
            except Exception as exc:
                logger.exception("Task {task_id} failed: {error}", task_id=task_id, error=exc)
                task.status = TaskStatusEnum.FAILED
                task.error_message = str(exc)
                task.progress = 100
            finally:
                session.flush()

    def fetch_status(self, task_id: str) -> TaskStatus:
        with session_scope() as session:
            task = session.get(TaskRecord, task_id)
            if task is None:
                raise TaskNotFoundError(task_id)
            # Eager load results
            _ = task.results  # noqa: F841
            status = self.build_status(task)
            return status

    def resolve_download_path(self, task_id: str, token: str, fmt: str) -> Path:
        with session_scope() as session:
            stmt = select(TaskResultRecord).where(
                TaskResultRecord.task_id == task_id,
                TaskResultRecord.format == fmt,
                TaskResultRecord.download_token == token,
            )
            result = session.scalars(stmt).first()
            if result is None:
                raise TaskNotFoundError(task_id)

            absolute = self.results_root / result.relative_path
            if not absolute.exists():
                raise FileNotFoundError(absolute)
            return absolute


task_service = TaskService()


