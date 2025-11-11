from __future__ import annotations

from pathlib import Path

import pytest

from app.services.command_runner import CommandResult
from app.services.conversion_pipeline import ConversionPipeline, ConversionResult, ConversionError


class DummyRunner:
    def run(self, command, **_: object) -> CommandResult:  # type: ignore[override]
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


@pytest.fixture(autouse=True)
def patch_command_availability(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.conversion_pipeline.CommandRunner.is_available", lambda _: True)


def test_conversion_pipeline_generates_requested_formats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_docx = tmp_path / "source.docx"
    source_docx.write_text("dummy docx content", encoding="utf-8")

    pipeline = ConversionPipeline(command_runner=DummyRunner())  # type: ignore[arg-type]
    results = pipeline.convert_docx(
        source_docx,
        ["docx", "pdf", "html", "markdown"],
        workdir=tmp_path / "outputs",
    )

    assert {result.format for result in results} == {"docx", "pdf", "html", "markdown"}
    for result in results:
        assert result.output_path.exists()


def test_conversion_pipeline_rejects_unsupported_format(tmp_path: Path) -> None:
    source_docx = tmp_path / "source.docx"
    source_docx.write_text("dummy", encoding="utf-8")

    pipeline = ConversionPipeline(command_runner=DummyRunner())  # type: ignore[arg-type]

    with pytest.raises(ConversionError):
        pipeline.convert_docx(source_docx, ["pptx"], workdir=tmp_path / "outputs")


