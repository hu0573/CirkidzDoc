#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import date
from pathlib import Path

from docx import Document
from docxtpl import DocxTemplate


WORKSPACE = Path("/workspace")
TMP_DIR = Path(os.environ.get("RENDER_TMP_DIR", WORKSPACE / "tmp"))
OUTPUT_DIR = Path(os.environ.get("RENDER_OUTPUT_DIR", WORKSPACE / "output"))


def ensure_directories() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_template(template_path: Path) -> None:
    if template_path.exists():
        return
    doc = Document()
    doc.add_heading("Sample Service Agreement", level=1)
    doc.add_paragraph("Party A: {{ party_a }}")
    doc.add_paragraph("Party B: {{ party_b }}")
    doc.add_paragraph("Sign Date: {{ sign_date }}")
    doc.add_paragraph("")
    doc.add_paragraph("Key Terms Summary:")
    doc.add_paragraph("1. Service Scope: {{ clause_1 }}")
    doc.add_paragraph("2. Pricing Terms: {{ clause_2 }}")
    doc.add_paragraph("3. Contact Information: {{ contact }}")
    doc.add_paragraph("")
    doc.add_paragraph("(The automated rendering pipeline produces all content above.)")
    doc.save(template_path)


def render_docx(template_path: Path, output_path: Path) -> dict:
    context = {
        "party_a": "Cirkidz Tech Ltd.",
        "party_b": "Sample Client",
        "sign_date": date.today().isoformat(),
        "clause_1": "Provide automated document template filling and format conversion services.",
        "clause_2": "Bill based on actual usage; waive service fees during the pilot stage.",
        "contact": "support@example.com",
    }
    template = DocxTemplate(str(template_path))
    template.render(context)
    template.save(output_path)
    return context


def convert_with_libreoffice(docx_path: Path, output_dir: Path) -> Path:
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf:writer_pdf_Export",
            str(docx_path),
            "--outdir",
            str(output_dir),
        ],
        check=True,
    )
    return output_dir / f"{docx_path.stem}.pdf"


def convert_with_pandoc(docx_path: Path, output_dir: Path, fmt: str) -> Path:
    target = output_dir / f"{docx_path.stem}.{fmt}"
    subprocess.run(
        [
            "pandoc",
            str(docx_path),
            "-o",
            str(target),
        ],
        check=True,
    )
    return target


def summarize(results: dict) -> None:
    print(json.dumps(results, indent=2, ensure_ascii=False))


def main() -> None:
    ensure_directories()
    template_path = TMP_DIR / "sample_template.docx"
    build_template(template_path)

    rendered_docx = OUTPUT_DIR / "sample_rendered.docx"
    context = render_docx(template_path, rendered_docx)

    pdf_path = convert_with_libreoffice(rendered_docx, OUTPUT_DIR)
    html_path = convert_with_pandoc(rendered_docx, OUTPUT_DIR, "html")
    md_path = convert_with_pandoc(rendered_docx, OUTPUT_DIR, "md")

    summarize(
        {
            "context": context,
            "outputs": {
                "docx": str(rendered_docx),
                "pdf": str(pdf_path),
                "html": str(html_path),
                "markdown": str(md_path),
            },
        }
    )


if __name__ == "__main__":
    main()

