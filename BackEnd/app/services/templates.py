from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from loguru import logger

from app.core.config import settings
from app.models.templates import TemplateMetadata


class TemplateNotFoundError(KeyError):
    """
    模板不存在时抛出的异常。
    """


def _load_metadata_file(metadata_path: Path) -> TemplateMetadata:
    """
    将 metadata.json 转换为 TemplateMetadata。
    """

    with metadata_path.open(encoding="utf-8") as fp:
        payload = json.load(fp)

    metadata = TemplateMetadata.model_validate(payload)
    logger.debug("已加载模板元数据: {template_id}", template_id=metadata.id)
    return metadata


def _build_registry(template_root: Path) -> dict[str, TemplateMetadata]:
    registry: dict[str, TemplateMetadata] = {}

    if not template_root.exists():
        logger.warning("模板目录不存在: {template_root}", template_root=template_root.as_posix())
        return registry

    for metadata_path in template_root.glob("*/metadata.json"):
        metadata = _load_metadata_file(metadata_path)
        registry[metadata.id] = metadata

    logger.info(
        "模板注册表加载完成，共 {count} 个模板",
        count=len(registry),
    )

    return registry


@lru_cache(maxsize=1)
def _cached_registry(template_root: str) -> dict[str, TemplateMetadata]:
    """
    使用 LRU 缓存避免频繁读取磁盘。
    """

    return _build_registry(Path(template_root))


class TemplateRepository:
    """
    模板仓库封装，提供查询与缓存刷新能力。
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
        清理缓存，下次读取时重新加载磁盘。
        """

        _cached_registry.cache_clear()
        logger.info("模板缓存已刷新: {template_root}", template_root=self.template_root.as_posix())
        # 预热缓存以避免首个请求的延迟
        _cached_registry(str(self.template_root))


template_repository = TemplateRepository()

