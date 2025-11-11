from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pikepdf
from loguru import logger
from pdfrw import PdfDict, PdfName, PdfReader, PdfString, PdfWriter

from app.core.config import settings
from app.services.command_runner import CommandRunner, CommandExecutionError
from app.services.toolkit_bridge import ToolkitPathError, host_to_toolkit_path, run_in_toolkit


PDF_CHECKBOX_ON = PdfName("Yes")
PDF_CHECKBOX_OFF = PdfName("Off")


@dataclass(slots=True)
class PdfRenderOptions:
    flatten: bool = False
    pdfa: bool = False
    password: str | None = None


class PdfRenderService:
    """
    PDF form filling service built on top of pdfrw and pikepdf.
    """

    def __init__(self, *, command_runner: CommandRunner | None = None) -> None:
        self.command_runner = command_runner or CommandRunner()

    @staticmethod
    def _decode_field_name(raw: Any) -> str | None:
        if raw is None:
            return None
        text = str(raw)
        if text.startswith("(") and text.endswith(")"):
            return text[1:-1]
        return text

    @staticmethod
    def _apply_checkbox(annotation: PdfDict, value: bool) -> None:
        annotation.update(
            PdfDict(
                AS=PDF_CHECKBOX_ON if value else PDF_CHECKBOX_OFF,
                V=PDF_CHECKBOX_ON if value else PDF_CHECKBOX_OFF,
            )
        )

    @staticmethod
    def _apply_text(annotation: PdfDict, value: Any) -> None:
        annotation.update(PdfDict(V=PdfString.encode(str(value))))
        if "/AP" in annotation:
            del annotation["/AP"]

    def _fill_fields(self, pdf_path: Path, data: dict[str, Any]) -> PdfReader:
        template_pdf = PdfReader(str(pdf_path))
        if not template_pdf.Root.AcroForm:
            logger.warning("PDF template is missing an AcroForm; skipping field population: {pdf}", pdf=pdf_path)
            return template_pdf

        if template_pdf.Root.AcroForm.get("NeedAppearances") != PdfName("true"):
            template_pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfName("true")))

        for page in template_pdf.pages:
            annotations = page.Annots
            if not annotations:
                continue

            for annotation in annotations:
                if annotation.Subtype != PdfName("Widget"):
                    continue
                field_name = self._decode_field_name(annotation.T)
                if not field_name or field_name not in data:
                    continue

                value = data[field_name]
                if isinstance(value, bool):
                    self._apply_checkbox(annotation, value)
                else:
                    self._apply_text(annotation, value)

        return template_pdf

    def _flatten(self, pdf_path: Path) -> None:
        temp_output = pdf_path.with_suffix(".flatten.tmp.pdf")
        if settings.use_toolkit_container:
            try:
                run_in_toolkit(
                    self.command_runner,
                    (
                        "qpdf",
                        "--flatten-annotations=print",
                        host_to_toolkit_path(pdf_path),
                        host_to_toolkit_path(temp_output),
                    ),
                    timeout=120,
                )
            except ToolkitPathError as exc:
                logger.warning("qpdf flatten skipped: {error}", error=exc)
                return
            except CommandExecutionError as exc:
                logger.error("qpdf flatten failed inside toolkit: {error}", error=exc)
                temp_output.unlink(missing_ok=True)
                return
        elif not CommandRunner.is_available("qpdf"):
            logger.warning("qpdf is unavailable; cannot flatten annotations.")
            return
        else:
            try:
                self.command_runner.run(
                    (
                        "qpdf",
                        "--flatten-annotations=print",
                        pdf_path.as_posix(),
                        temp_output.as_posix(),
                    ),
                    timeout=120,
                )
            except CommandExecutionError as exc:
                logger.error("qpdf flatten failed: {error}", error=exc)
                temp_output.unlink(missing_ok=True)
                return
        if temp_output.exists():
            temp_output.replace(pdf_path)

    def _apply_pdfa(self, pdf_path: Path) -> None:
        try:
            with pikepdf.Pdf.open(pdf_path) as pdf:
                pdf.make_compatible(pikepdf.PdfCompatibility.PDFA_2_U)
                pdf.save(pdf_path)
        except (pikepdf.PdfError, AttributeError) as exc:
            logger.warning("pikepdf PDF/A conversion failed: {error}", error=exc)
            temp_output = pdf_path.with_suffix(".pdfa.tmp.pdf")

            if settings.use_toolkit_container:
                try:
                    run_in_toolkit(
                        self.command_runner,
                        (
                            "gs",
                            "-dPDFA=2",
                            "-dBATCH",
                            "-dNOPAUSE",
                            "-sColorConversionStrategy=UseDeviceIndependentColor",
                            "-sDEVICE=pdfwrite",
                            "-dPDFACompatibilityPolicy=1",
                            f"-sOutputFile={host_to_toolkit_path(temp_output)}",
                            host_to_toolkit_path(pdf_path),
                        ),
                        timeout=180,
                    )
                    temp_output.replace(pdf_path)
                except ToolkitPathError as path_error:
                    logger.error("Ghostscript PDF/A skipped due to path error: {error}", error=path_error)
                    temp_output.unlink(missing_ok=True)
                except CommandExecutionError as gs_error:
                    logger.error("Ghostscript PDF/A conversion failed in toolkit: {error}", error=gs_error)
                    temp_output.unlink(missing_ok=True)
            elif CommandRunner.is_available("gs"):
                try:
                    self.command_runner.run(
                        (
                            "gs",
                            "-dPDFA=2",
                            "-dBATCH",
                            "-dNOPAUSE",
                            "-sColorConversionStrategy=UseDeviceIndependentColor",
                            "-sDEVICE=pdfwrite",
                            "-dPDFACompatibilityPolicy=1",
                            f"-sOutputFile={temp_output.as_posix()}",
                            pdf_path.as_posix(),
                        ),
                        timeout=180,
                    )
                    temp_output.replace(pdf_path)
                except CommandExecutionError as gs_error:
                    logger.error("Ghostscript PDF/A conversion failed: {error}", error=gs_error)
                    temp_output.unlink(missing_ok=True)
            else:
                logger.error("Missing PDF/A conversion tools (pikepdf/ghostscript); skipping.")

    def _apply_password(self, pdf_path: Path, password: str) -> None:
        temp_output = pdf_path.with_suffix(".encrypt.tmp.pdf")
        if settings.use_toolkit_container:
            try:
                run_in_toolkit(
                    self.command_runner,
                    (
                        "qpdf",
                        host_to_toolkit_path(pdf_path),
                        host_to_toolkit_path(temp_output),
                        "--encrypt",
                        password,
                        password,
                        "256",
                        "--",
                    ),
                    timeout=120,
                )
            except ToolkitPathError as exc:
                logger.warning("qpdf encryption skipped: {error}", error=exc)
                temp_output.unlink(missing_ok=True)
                return
            except CommandExecutionError as exc:
                logger.error("qpdf encryption failed in toolkit: {error}", error=exc)
                temp_output.unlink(missing_ok=True)
                return
        elif not CommandRunner.is_available("qpdf"):
            logger.warning("qpdf is unavailable; cannot encrypt PDF.")
            return
        else:
            try:
                self.command_runner.run(
                    (
                        "qpdf",
                        pdf_path.as_posix(),
                        temp_output.as_posix(),
                        "--encrypt",
                        password,
                        password,
                        "256",
                        "--",
                    ),
                    timeout=120,
                )
            except CommandExecutionError as exc:
                logger.error("qpdf encryption failed: {error}", error=exc)
                temp_output.unlink(missing_ok=True)
                return
        if temp_output.exists():
            temp_output.replace(pdf_path)

    def render(
        self,
        template_path: Path,
        data: dict[str, Any],
        *,
        output_path: Path,
        options: PdfRenderOptions | None = None,
    ) -> Path:
        if not template_path.exists():
            raise FileNotFoundError(f"PDF template does not exist: {template_path}")

        logger.info("Rendering PDF template: {template}", template=template_path.as_posix())

        filled_pdf = self._fill_fields(template_path, data)
        writer = PdfWriter()
        writer.trailer = filled_pdf
        writer.write(output_path.as_posix())

        options = options or PdfRenderOptions()

        if options.flatten:
            self._flatten(output_path)
        if options.pdfa:
            self._apply_pdfa(output_path)
        if options.password:
            self._apply_password(output_path, options.password)

        logger.info("PDF render complete. Output file: {output}", output=output_path.as_posix())
        return output_path


