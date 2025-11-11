from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_dependency_status(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.health.collect_dependency_status",
        lambda: [
            # 使用命名元组或简单对象模拟
            type("Status", (), {"name": "pandoc", "available": True}),
            type("Status", (), {"name": "libreoffice", "available": False}),
        ],
    )

    client = TestClient(app)
    resp = client.get("/health")
    payload = resp.json()

    assert resp.status_code == 200
    assert payload["status"] == "degraded"
    assert payload["dependencies"] == {"pandoc": True, "libreoffice": False}


