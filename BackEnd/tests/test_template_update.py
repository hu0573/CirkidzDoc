from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.templates import template_repository


def _write_metadata(path: Path, *, field_types: list[tuple[str, str]]) -> None:
    metadata = {
        "id": path.parent.name,
        "name": "Demo Template",
        "description": "Sample description",
        "entry": "demo.docx",
        "fields": [{"name": field, "type": field_type} for field, field_type in field_types],
    }
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def _prepare_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkey_template_dir = tmp_path / "demo"
    monkey_template_dir.mkdir()
    _write_metadata(monkey_template_dir / "metadata.json", field_types=[("first_name", "string"), ("age", "number")])
    (monkey_template_dir / "demo.docx").write_text("placeholder")

    monkeypatch.setattr(settings, "template_root_relative", tmp_path)
    monkeypatch.setattr(template_repository, "template_root", settings.template_root)
    template_repository.refresh()


def test_update_template_metadata_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_repository(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.patch(
        "/api/templates/demo",
        json={
            "description": "Updated description",
            "fields": [
                {"name": "first_name", "type": "string"},
                {"name": "age", "type": "integer"},
            ],
        },
    )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["template"]["description"] == "Updated description"
    assert body["template"]["fields"][1]["type"] == "integer"

    metadata_file = tmp_path / "demo" / "metadata.json"
    payload = json.loads(metadata_file.read_text(encoding="utf-8"))
    assert payload["description"] == "Updated description"
    assert payload["fields"][1]["type"] == "integer"


def test_update_template_metadata_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_repository(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.patch(
        "/api/templates/demo",
        json={
            "fields": [
                {"name": "first_name", "type": "string"},
                # Missing entry for field "age"
            ],
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Field updates must reference all existing fields" in response.json()["detail"]


def test_delete_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_repository(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.delete("/api/templates/demo")

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert not (tmp_path / "demo").exists()


def test_delete_template_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_repository(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.delete("/api/templates/missing")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == "Template missing does not exist"

