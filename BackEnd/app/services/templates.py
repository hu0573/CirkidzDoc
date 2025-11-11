from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile

from loguru import logger

from app.core.config import settings
from app.models.templates import FieldSchema, TemplateMetadata, TemplateUpdateRequest


class TemplateNotFoundError(KeyError):
    """
    Raised when the requested template does not exist.
    """


def _load_metadata_file(metadata_path: Path) -> TemplateMetadata:
    """
    Load a metadata.json file and convert it into a TemplateMetadata instance.
    """

    with metadata_path.open(encoding="utf-8") as fp:
        payload = json.load(fp)

    metadata = TemplateMetadata.model_validate(payload)
    logger.debug("Loaded template metadata: {template_id}", template_id=metadata.id)
    return metadata


def _build_registry(template_root: Path) -> dict[str, TemplateMetadata]:
    registry: dict[str, TemplateMetadata] = {}

    if not template_root.exists():
        logger.warning("Template directory does not exist: {template_root}", template_root=template_root.as_posix())
        return registry

    for metadata_path in template_root.glob("*/metadata.json"):
        metadata = _load_metadata_file(metadata_path)
        registry[metadata.id] = metadata

    logger.info(
        "Template registry loaded with {count} templates",
        count=len(registry),
    )

    return registry


@lru_cache(maxsize=1)
def _cached_registry(template_root: str) -> dict[str, TemplateMetadata]:
    """
    Cache the template registry with LRU to avoid frequent disk reads.
    """

    return _build_registry(Path(template_root))


class TemplateRepository:
    """
    Repository wrapper that provides lookup and cache refresh capabilities for templates.
    """

    def __init__(self, template_root: Path | None = None) -> None:
        self.template_root = template_root or settings.template_root

    def list_templates(self) -> list[TemplateMetadata]:
        registry = _cached_registry(str(self.template_root))
        return list(registry.values())

    def get_template(self, template_id: str) -> TemplateMetadata:
        registry = _cached_registry(str(self.template_root))
        try:
            return registry[template_id]
        except KeyError as exc:
            raise TemplateNotFoundError(template_id) from exc

    def _metadata_path(self, template_id: str) -> Path:
        path = self.template_root / template_id / "metadata.json"
        if not path.exists():
            raise TemplateNotFoundError(template_id)
        return path

    def delete_template(self, template_id: str) -> None:
        template_dir = self.template_root / template_id
        if not template_dir.exists():
            raise TemplateNotFoundError(template_id)
        shutil.rmtree(template_dir, ignore_errors=False)
        self.refresh()

    def refresh(self) -> None:
        """
        Clear the cache so that the next read reloads from disk.
        """

        _cached_registry.cache_clear()
        logger.info("Template cache refreshed: {template_root}", template_root=self.template_root.as_posix())
        # Warm the cache to avoid latency on the first request.
        _cached_registry(str(self.template_root))

    def save_template(self, metadata: TemplateMetadata) -> TemplateMetadata:
        """
        Persist template metadata to disk and refresh the cache.
        """

        metadata_path = self._metadata_path(metadata.id)
        metadata_path.write_text(
            json.dumps(metadata.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.refresh()
        return self.get_template(metadata.id)


template_repository = TemplateRepository()


class TemplateCreationError(ValueError):
    """Raised when a template upload cannot be processed."""


class TemplateUpdateError(ValueError):
    """Raised when template metadata updates are invalid."""


@dataclass(slots=True)
class TemplateCreationResult:
    metadata: TemplateMetadata
    template_dir: Path
    metadata_path: Path


_MAX_TEMPLATE_SIZE_BYTES = 20 * 1024 * 1024
_SUPPORTED_TEMPLATE_SUFFIXES = {".docx"}
_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([^\{\}]+?)\s*\}\}")


def _normalise_template_id(raw: str) -> str:
    candidate = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return candidate or "template"


def _ensure_unique_template_id(template_root: Path, desired: str) -> str:
    candidate = desired
    suffix = 1
    while (template_root / candidate).exists():
        candidate = f"{desired}-{suffix}"
        suffix += 1
    return candidate


def _derive_template_name(file_name: str) -> str:
    base = Path(file_name).stem.replace("_", " ").replace("-", " ").strip()
    if not base:
        return "New Template"
    return base.title()


def _extract_placeholders(docx_path: Path) -> list[str]:
    placeholders: list[str] = []
    seen: set[str] = set()

    try:
        with ZipFile(docx_path) as archive:
            for name in archive.namelist():
                if not name.startswith("word/") or not name.endswith(".xml"):
                    continue
                xml = archive.read(name).decode("utf-8", errors="ignore")
                for match in _PLACEHOLDER_PATTERN.finditer(xml):
                    raw = match.group(1).split("|", 1)[0].strip()
                    if not raw:
                        continue
                    if raw not in seen:
                        seen.add(raw)
                        placeholders.append(raw)
    except Exception as exc:  # noqa: BLE001
        raise TemplateCreationError("Failed to analyse template placeholders.") from exc

    return placeholders


def create_template_from_upload(
    *,
    file_name: str,
    file_bytes: bytes,
    template_root: Path | None = None,
    description: str | None = None,
) -> TemplateCreationResult:
    if not file_name:
        raise TemplateCreationError("Uploaded file must include a filename.")

    suffix = Path(file_name).suffix.lower()
    if suffix not in _SUPPORTED_TEMPLATE_SUFFIXES:
        raise TemplateCreationError("Only .docx templates are supported at this time.")

    if not file_bytes:
        raise TemplateCreationError("Uploaded file is empty.")

    if len(file_bytes) > _MAX_TEMPLATE_SIZE_BYTES:
        raise TemplateCreationError("Uploaded file exceeds the 20MB limit.")

    root = template_root or settings.template_root
    root.mkdir(parents=True, exist_ok=True)

    desired_id = _normalise_template_id(Path(file_name).stem)
    template_id = _ensure_unique_template_id(root, desired_id)
    template_dir = root / template_id

    entry_name = Path(file_name).name or f"{template_id}{suffix}"
    entry_path = template_dir / entry_name
    metadata_path = template_dir / "metadata.json"

    template_dir.mkdir(parents=True, exist_ok=False)

    try:
        entry_path.write_bytes(file_bytes)
        placeholders = _extract_placeholders(entry_path)
        fields = [FieldSchema(name=placeholder, type="string") for placeholder in placeholders]

        metadata = TemplateMetadata(
            id=template_id,
            name=_derive_template_name(file_name),
            description=description or "",
            entry=entry_name,
            fields=fields,
        )

        metadata_path.write_text(
            json.dumps(metadata.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(template_dir, ignore_errors=True)
        raise TemplateCreationError(str(exc)) from exc

    logger.info(
        "Created template {template_id} with {field_count} fields",
        template_id=template_id,
        field_count=len(fields),
    )

    return TemplateCreationResult(metadata=metadata, template_dir=template_dir, metadata_path=metadata_path)


def update_template_metadata(template_id: str, payload: TemplateUpdateRequest) -> TemplateMetadata:
    """
    Update template metadata and persist the updated model to disk.
    """

    try:
        current = template_repository.get_template(template_id)
    except TemplateNotFoundError as exc:
        raise exc

    updated = current.model_copy(deep=True)

    if payload.name is not None:
        updated.name = payload.name
    if payload.description is not None:
        updated.description = payload.description

    if payload.fields is not None:
        existing_fields = updated.fields
        incoming_names = [field.name for field in payload.fields]
        expected_names = [field.name for field in existing_fields]

        if set(incoming_names) != set(expected_names):
            raise TemplateUpdateError("Field updates must reference all existing fields by name.")

        seen: set[str] = set()
        updates_lookup = {field.name: field for field in payload.fields}
        new_fields: list[FieldSchema] = []

        for field in existing_fields:
            if field.name not in updates_lookup:
                raise TemplateUpdateError(f"Missing update entry for field '{field.name}'.")
            if field.name in seen:
                raise TemplateUpdateError(f"Duplicate field entry detected: '{field.name}'.")
            seen.add(field.name)
            replacement = updates_lookup[field.name]
            new_fields.append(FieldSchema(name=replacement.name, type=replacement.type))

        updated.fields = new_fields

    return template_repository.save_template(updated)


def delete_template(template_id: str) -> None:
    """
    Remove a template directory and refresh the registry.
    """

    template_repository.delete_template(template_id)

