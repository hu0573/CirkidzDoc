from __future__ import annotations

from pathlib import Path

import pytest
from pdfrw import PdfDict, PdfName, PdfString

from app.services.pdf_renderer import PDF_CHECKBOX_OFF, PDF_CHECKBOX_ON, PdfRenderOptions, PdfRenderService


class DummyWriter:
    def __init__(self) -> None:
        self.trailer = None

    def write(self, output_path: str) -> None:
        Path(output_path).write_bytes(b"%PDF-1.4\n%%EOF")


@pytest.fixture(autouse=True)
def disable_external_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.pdf_renderer.CommandRunner.is_available", lambda _: False)


def test_pdf_renderer_fills_text_and_checkbox_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    template_path = tmp_path / "template.pdf"
    template_path.write_bytes(b"%PDF-1.4 dummy")
    output_path = tmp_path / "output.pdf"

    text_annotation = PdfDict(Subtype=PdfName("Widget"), T=PdfString.encode("full_name"))
    checkbox_annotation = PdfDict(Subtype=PdfName("Widget"), T=PdfString.encode("agreement"))
    page = PdfDict(Annots=[text_annotation, checkbox_annotation])
    acro_form = PdfDict(Fields=[text_annotation, checkbox_annotation])

    class FakePdf:
        Root = PdfDict(AcroForm=acro_form)
        pages = [page]

    monkeypatch.setattr("app.services.pdf_renderer.PdfReader", lambda _: FakePdf())
    monkeypatch.setattr("app.services.pdf_renderer.PdfWriter", DummyWriter)

    service = PdfRenderService()
    service.render(
        template_path,
        {
            "full_name": "John Doe",
            "agreement": True,
        },
        output_path=output_path,
        options=PdfRenderOptions(),
    )

    assert output_path.exists()
    assert text_annotation.V == PdfString.encode("John Doe")
    assert checkbox_annotation.V == PDF_CHECKBOX_ON
    assert checkbox_annotation.AS == PDF_CHECKBOX_ON
    assert FakePdf.Root.AcroForm.NeedAppearances == PdfName("true")


def test_pdf_renderer_handles_false_checkbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    template_path = tmp_path / "template.pdf"
    template_path.write_bytes(b"%PDF-1.4 dummy")
    output_path = tmp_path / "output.pdf"

    checkbox_annotation = PdfDict(Subtype=PdfName("Widget"), T=PdfString.encode("agreement"))
    page = PdfDict(Annots=[checkbox_annotation])
    acro_form = PdfDict(Fields=[checkbox_annotation])

    class FakePdf:
        Root = PdfDict(AcroForm=acro_form)
        pages = [page]

    monkeypatch.setattr("app.services.pdf_renderer.PdfReader", lambda _: FakePdf())
    monkeypatch.setattr("app.services.pdf_renderer.PdfWriter", DummyWriter)

    service = PdfRenderService()
    service.render(
        template_path,
        {
            "agreement": False,
        },
        output_path=output_path,
        options=PdfRenderOptions(),
    )

    assert checkbox_annotation.V == PDF_CHECKBOX_OFF
    assert checkbox_annotation.AS == PDF_CHECKBOX_OFF


