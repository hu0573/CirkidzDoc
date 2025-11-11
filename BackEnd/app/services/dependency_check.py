from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.command_runner import ensure_commands_available


@dataclass(slots=True)
class DependencyStatus:
    name: str
    available: bool


def collect_dependency_status() -> list[DependencyStatus]:
    """
    检查外部依赖（Pandoc、LibreOffice、qpdf、ghostscript 等）的可用性。
    """

    availability = ensure_commands_available(settings.dependency_commands)
    return [DependencyStatus(name=name, available=is_available) for name, is_available in availability.items()]


