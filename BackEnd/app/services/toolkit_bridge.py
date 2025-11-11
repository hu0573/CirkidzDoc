from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Sequence

from app.core.config import settings
from app.services.command_runner import CommandRunner, CommandResult


class ToolkitPathError(RuntimeError):
    """
    Raised when a host path cannot be mapped into the toolkit container.
    """


def _shared_roots() -> tuple[Path, Path]:
    return settings.render_tmp_dir.resolve(), settings.render_output_dir.resolve()


def host_to_toolkit_path(path: Path) -> str:
    """
    Convert an absolute host path inside the shared render directories to the toolkit container path.
    """

    resolved = path.resolve()
    tmp_root, output_root = _shared_roots()

    if resolved == tmp_root:
        return settings.toolkit_tmp_dir
    if resolved == output_root:
        return settings.toolkit_output_dir

    if resolved.is_relative_to(tmp_root):
        relative = resolved.relative_to(tmp_root)
        return str(PurePosixPath(settings.toolkit_tmp_dir) / PurePosixPath(relative.as_posix()))

    if resolved.is_relative_to(output_root):
        relative = resolved.relative_to(output_root)
        return str(PurePosixPath(settings.toolkit_output_dir) / PurePosixPath(relative.as_posix()))

    raise ToolkitPathError(
        f"Path {resolved} is not inside the shared render directories {tmp_root} or {output_root}."
    )


def run_in_toolkit(
    runner: CommandRunner,
    command: Sequence[str],
    *,
    timeout: int | None = None,
) -> CommandResult:
    """
    Execute a command inside the toolkit container using docker compose exec.
    """

    if not settings.toolkit_compose_file:
        raise RuntimeError("Toolkit compose file is not configured.")

    full_command: list[str] = [
        "docker",
        "compose",
        "-f",
        str(settings.toolkit_compose_file),
        "exec",
        "-T",
        settings.toolkit_service_name,
        *command,
    ]
    return runner.run(full_command, timeout=timeout)

