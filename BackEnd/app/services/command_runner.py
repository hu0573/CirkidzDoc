from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from loguru import logger


class CommandExecutionError(RuntimeError):
    """
    Raised when executing an external command fails.
    """

    def __init__(self, command: Sequence[str], returncode: int, stdout: str, stderr: str) -> None:
        self.command = list(command)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            f"Command execution failed (exit={returncode}): {shlex.join(self.command)}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int


class CommandRunner:
    """
    Manage external command invocation with consistent logging and error handling.
    """

    def __init__(self, *, env: dict[str, str] | None = None, cwd: Path | None = None) -> None:
        self.env = {**os.environ, **(env or {})}
        self.cwd = cwd

    @staticmethod
    def is_available(command: str) -> bool:
        """
        Check whether the command exists in PATH.
        """

        return shutil.which(command) is not None

    def run(
        self,
        command: Sequence[str],
        *,
        timeout: int | None = None,
        check: bool = True,
        capture_output: bool = True,
        allow_missing: bool = False,
        extra_env: dict[str, str] | None = None,
    ) -> CommandResult:
        """
        Execute an external command, capturing output by default.
        """

        if allow_missing and not self.is_available(command[0]):
            raise FileNotFoundError(f"Command not found: {command[0]}")

        env = self.env.copy()
        if extra_env:
            env.update(extra_env)

        logger.debug("Executing external command: {command}", command=shlex.join(command))

        completed = subprocess.run(
            list(command),
            timeout=timeout,
            check=False,
            capture_output=capture_output,
            env=env,
            cwd=self.cwd,
            text=True,
        )

        result = CommandResult(
            command=tuple(command),
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            returncode=completed.returncode,
        )

        if check and completed.returncode != 0:
            raise CommandExecutionError(command, completed.returncode, result.stdout, result.stderr)

        return result


def ensure_commands_available(commands: Iterable[str]) -> dict[str, bool]:
    """
    Check whether the provided commands exist.
    """

    availability: dict[str, bool] = {}
    for command in commands:
        availability[command] = CommandRunner.is_available(command)
        logger.debug("Command {command} available: {available}", command=command, available=availability[command])
    return availability


