#!/usr/bin/env python3
"""
Launch the CirkidzDoc frontend and backend development environment.

- Start the FastAPI backend and Vite frontend development servers by default.
- Ensure the Docker CLI is available and the `cirkidzdoc/toolkit:dev` image exists;
  run `docker compose build` to build the rendering toolkit image if missing.

Usage:
    python run_project.py                 # Start backend + frontend + rendering toolkit Docker
    python run_project.py --backend-only  # Backend only (still starts the rendering toolkit Docker)
    python run_project.py --frontend-only # Frontend only (still starts the rendering toolkit Docker)

Press Ctrl+C to terminate; the script will attempt to shut down all subprocesses gracefully.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from shutil import which
from pathlib import Path
from typing import List, Optional


REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "BackEnd"
FRONTEND_DIR = REPO_ROOT / "FrontEnd"
INFRA_DIR = REPO_ROOT / "infra"


class ManagedProcess:
    def __init__(self, name: str, command: List[str], cwd: Path, env: Optional[dict] = None):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env or os.environ.copy()
        self.proc: Optional[subprocess.Popen[bytes]] = None

    def start(self) -> None:
        print(f"[START] {self.name}: {' '.join(self.command)} (cwd={self.cwd})")
        self.proc = subprocess.Popen(
            self.command,
            cwd=str(self.cwd),
            env=self.env,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    def stop(self) -> None:
        if not self.proc:
            return
        if self.proc.poll() is not None:
            return
        print(f"[STOP] {self.name}")
        try:
            self.proc.send_signal(signal.SIGINT)
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print(f"[WARN] {self.name} did not exit within 10 seconds, attempting to kill it.")
            self.proc.kill()


def run_docker_toolkit(detach: bool) -> subprocess.CompletedProcess[bytes]:
    compose_file = INFRA_DIR / "docker-compose.yml"
    ensure_docker_available()
    ensure_toolkit_image(compose_file)
    command = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "up",
        "toolkit",
    ]
    if detach:
        command.insert(-1, "-d")

    print(f"[START] Docker toolkit: {' '.join(command)}")
    return subprocess.run(command, cwd=str(INFRA_DIR), check=True)


def ensure_docker_available() -> None:
    if which("docker") is None:
        raise RuntimeError("Docker is not available. Please install it and ensure the `docker` command is usable.")


def ensure_toolkit_image(compose_file: Path) -> None:
    target_image = "cirkidzdoc/toolkit:dev"
    inspect_command = ["docker", "image", "inspect", target_image]
    result = subprocess.run(inspect_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        return

    print(f"[BUILD] Image {target_image} not found. Running docker compose build.")
    build_command = ["docker", "compose", "-f", str(compose_file), "build", "toolkit"]
    subprocess.run(build_command, cwd=str(INFRA_DIR), check=True)


def ensure_npm_available() -> None:
    if which("npm") is None:
        raise RuntimeError("npm is not available. Please install Node.js and ensure the `npm` command is usable.")


def run_npm_install(frontend_dir: Path, args: List[str]) -> None:
    command = ["npm", "install", *args]
    print(f"[RUN] {' '.join(command)} (cwd={frontend_dir})")
    subprocess.run(command, cwd=str(frontend_dir), check=True)


def ensure_frontend_dependencies() -> None:
    ensure_npm_available()

    node_modules_dir = FRONTEND_DIR / "node_modules"
    tailwind_dir = node_modules_dir / "tailwindcss"
    tailwind_vite_dir = node_modules_dir / "@tailwindcss" / "vite"

    if not node_modules_dir.exists():
        print("[DEPENDENCY] Frontend node_modules missing. Running npm install.")
        run_npm_install(FRONTEND_DIR, [])
    else:
        package_lock = FRONTEND_DIR / "package-lock.json"
        if not package_lock.exists():
            print("[DEPENDENCY] package-lock.json missing; running npm install to ensure dependencies.")
            run_npm_install(FRONTEND_DIR, [])

    missing_tailwind_pkgs = []
    if not tailwind_dir.exists():
        missing_tailwind_pkgs.append("tailwindcss")
    if not tailwind_vite_dir.exists():
        missing_tailwind_pkgs.append("@tailwindcss/vite")

    if missing_tailwind_pkgs:
        print(f"[DEPENDENCY] Missing tailwind packages: {', '.join(missing_tailwind_pkgs)}. Installing.")
        run_npm_install(FRONTEND_DIR, missing_tailwind_pkgs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the CirkidzDoc frontend and backend development environment.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backend-only", action="store_true", help="Start only the backend service.")
    group.add_argument("--frontend-only", action="store_true", help="Start only the frontend service.")
    parser.add_argument("--backend-host", default="0.0.0.0", help="Backend listen address, defaults to 0.0.0.0.")
    parser.add_argument("--backend-port", default="8000", help="Backend listen port, defaults to 8000.")
    parser.add_argument("--frontend-host", default="0.0.0.0", help="Frontend listen address passed to Vite, defaults to 0.0.0.0.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    processes: List[ManagedProcess] = []

    start_backend = not args.frontend_only
    start_frontend = not args.backend_only

    try:
        run_docker_toolkit(detach=True)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] Failed to start toolkit: {exc}")
        return 1

    if start_backend:
        backend_cmd = [
            "uv",
            "run",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            args.backend_host,
            "--port",
            args.backend_port,
        ]
        processes.append(ManagedProcess("Backend FastAPI", backend_cmd, BACKEND_DIR))

    if start_frontend:
        try:
            ensure_frontend_dependencies()
        except RuntimeError as exc:
            print(f"[ERROR] {exc}")
            return 1
        except subprocess.CalledProcessError as exc:
            print(f"[ERROR] Failed to install frontend dependencies: {exc}")
            return 1

        frontend_cmd = ["npm", "run", "dev"]
        if args.frontend_host:
            frontend_cmd.extend(["--", "--host", args.frontend_host])
        processes.append(ManagedProcess("Frontend Vite", frontend_cmd, FRONTEND_DIR))

    if not processes:
        print("[HINT] No service selected. Use --backend-only / --frontend-only / default to start something.")
        return 0

    for proc in processes:
        proc.start()

    def handle_signal(signum, frame):  # type: ignore[override]
        print(f"\n[SIGNAL] Received {signum}. Cleaning up.")
        for p in processes:
            p.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while True:
            for proc in processes:
                if proc.proc and proc.proc.poll() is not None:
                    raise RuntimeError(f"{proc.name} exited early with return code {proc.proc.returncode}")
            signal.pause()
    except RuntimeError as err:
        print(f"[ERROR] {err}")
        for p in processes:
            p.stop()
        return 1
    except KeyboardInterrupt:
        print("\n[SIGNAL] Received Ctrl+C. Cleaning up.")
        for p in processes:
            p.stop()
        return 0


if __name__ == "__main__":
    sys.exit(main())

