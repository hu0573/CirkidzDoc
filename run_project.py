#!/usr/bin/env python3
"""
一键启动 CirkidzDoc 前后端开发环境的脚本。

- 默认启动 FastAPI 后端与前端 Vite 开发服务器。
- 可选启动渲染工具链 Docker（infra/toolkit）。

使用示例：
    python run_project.py                 # 启动后端 + 前端 + 渲染工具链 Docker
    python run_project.py --backend-only  # 仅后端（仍会启动渲染工具链 Docker）
    python run_project.py --frontend-only # 仅前端（仍会启动渲染工具链 Docker）

按 Ctrl+C 终止，脚本会尝试优雅关闭所有子进程。
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
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
        print(f"[启动] {self.name}: {' '.join(self.command)} (cwd={self.cwd})")
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
        print(f"[停止] {self.name}")
        try:
            self.proc.send_signal(signal.SIGINT)
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print(f"[警告] {self.name} 未在 10 秒内退出，尝试强制结束。")
            self.proc.kill()


def run_docker_toolkit(detach: bool) -> subprocess.CompletedProcess[bytes]:
    compose_file = INFRA_DIR / "docker-compose.yml"
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

    print(f"[启动] Docker toolkit: {' '.join(command)}")
    return subprocess.run(command, cwd=str(INFRA_DIR), check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动 CirkidzDoc 前后端开发环境")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backend-only", action="store_true", help="仅启动后端服务")
    group.add_argument("--frontend-only", action="store_true", help="仅启动前端服务")
    parser.add_argument("--backend-host", default="0.0.0.0", help="后端监听地址，默认 0.0.0.0")
    parser.add_argument("--backend-port", default="8000", help="后端监听端口，默认 8000")
    parser.add_argument("--frontend-host", default=None, help="前端监听地址，传递给 Vite，例如 0.0.0.0")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    processes: List[ManagedProcess] = []

    start_backend = not args.frontend_only
    start_frontend = not args.backend_only

    try:
        run_docker_toolkit(detach=True)
    except subprocess.CalledProcessError as exc:
        print(f"[错误] 启动 toolkit 失败：{exc}")
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
        processes.append(ManagedProcess("后端 FastAPI", backend_cmd, BACKEND_DIR))

    if start_frontend:
        frontend_cmd = ["npm", "run", "dev"]
        if args.frontend_host:
            frontend_cmd.extend(["--", "--host", args.frontend_host])
        processes.append(ManagedProcess("前端 Vite", frontend_cmd, FRONTEND_DIR))

    if not processes:
        print("[提示] 未选择任何服务，请使用 --backend-only / --frontend-only / 默认启动。")
        return 0

    for proc in processes:
        proc.start()

    def handle_signal(signum, frame):  # type: ignore[override]
        print(f"\n[信号] 收到 {signum}，开始清理。")
        for p in processes:
            p.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while True:
            for proc in processes:
                if proc.proc and proc.proc.poll() is not None:
                    raise RuntimeError(f"{proc.name} 提前退出，返回码 {proc.proc.returncode}")
            signal.pause()
    except RuntimeError as err:
        print(f"[错误] {err}")
        for p in processes:
            p.stop()
        return 1
    except KeyboardInterrupt:
        print("\n[信号] 收到 Ctrl+C，开始清理。")
        for p in processes:
            p.stop()
        return 0


if __name__ == "__main__":
    sys.exit(main())

