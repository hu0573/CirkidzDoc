from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse, parse_qs

import pytest
from fastapi.testclient import TestClient

from app.db.session import init_database, session_scope
from app.db.models import TaskRecord
from app.main import app
from app.services.command_runner import CommandResult
from app.services.task_service import task_service
from app.services.conversion_pipeline import ConversionPipeline


class DummyRunner:
    def run(self, command, **_: object):  # type: ignore[override]
        executable = command[0]
        if executable == "libreoffice":
            source = Path(command[4])
            outdir = Path(command[6])
            out_path = outdir / f"{source.stem}.pdf"
            out_path.write_bytes(b"%PDF-1.4 dummy")
        elif executable == "pandoc":
            out_path = Path(command[-1])
            out_path.write_text("converted content", encoding="utf-8")
        else:
            raise AssertionError(f"unexpected command: {command}")
        return CommandResult(command=tuple(command), stdout="", stderr="", returncode=0)


def setup_function() -> None:
    """
    确保每个测试前数据库为干净状态。
    """

    init_database()
    with session_scope() as session:
        session.query(TaskRecord).delete()

    results_dir = Path(task_service.results_root)
    if results_dir.exists():
        for child in results_dir.iterdir():
            if child.is_dir():
                import shutil

                shutil.rmtree(child, ignore_errors=True)


def test_render_task_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    task_service.results_root = tmp_path
    monkeypatch.setattr("app.services.conversion_pipeline.CommandRunner.is_available", lambda _: True)
    task_service.engine.conversion_pipeline = ConversionPipeline(command_runner=DummyRunner())  # type: ignore[arg-type]

    client = TestClient(app)

    payload = {
        "template_id": "example_contract",
        "data": {
            "party_a_name": "示例科技",
            "party_b_name": "合作伙伴",
            "sign_date": "2025-11-11",
        },
        "formats": ["docx", "pdf"],
    }

    response = client.post("/api/templates/render", json=payload)
    assert response.status_code == 202
    body = response.json()
    task_id = body["task_id"]
    assert body["status"] == "queued"

    # 手动触发任务执行，模拟后台任务完成流程
    task_service.process_task(task_id)

    status_resp = client.get(f"/api/templates/tasks/{task_id}")
    assert status_resp.status_code == 200
    status_body = status_resp.json()
    assert status_body["status"] == "succeeded"
    assert status_body["progress"] == 100
    assert len(status_body["results"]) >= 2

    download_entry = status_body["results"][0]
    download_url = download_entry["download_url"]
    parsed = urlparse(download_url)
    query = parse_qs(parsed.query)
    token = query["token"][0]

    download_resp = client.get(parsed.path, params={"token": token})
    assert download_resp.status_code == 200
    assert int(download_resp.headers.get("content-length", "0")) > 0


def test_unknown_task_status_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.conversion_pipeline.CommandRunner.is_available", lambda _: True)
    task_service.engine.conversion_pipeline = ConversionPipeline(command_runner=DummyRunner())  # type: ignore[arg-type]
    client = TestClient(app)
    resp = client.get("/api/templates/tasks/nonexistent")
    assert resp.status_code == 404


