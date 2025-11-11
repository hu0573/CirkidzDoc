from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from loguru import logger

from app.core.config import settings
from app.models.templates import TemplateMetadata


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

    def refresh(self) -> None:
        """
        Clear the cache so that the next read reloads from disk.
        """

        _cached_registry.cache_clear()
        logger.info("Template cache refreshed: {template_root}", template_root=self.template_root.as_posix())
        # Warm the cache to avoid latency on the first request.
        _cached_registry(str(self.template_root))


template_repository = TemplateRepository()

