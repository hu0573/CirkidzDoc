from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from loguru import logger

from app.core.config import settings
from app.models.templates import RenderRequest, TemplateMetadata
from app.services.command_runner import CommandRunner
from app.services.conversion_pipeline import ConversionPipeline, ConversionResult
from app.services.docx_renderer import DocxRenderService
from app.services.pdf_renderer import PdfRenderOptions, PdfRenderService
from app.services.templates import TemplateRepository, template_repository


@dataclass(slots=True)
class RenderOutcome:
    format: str
    file_path: Path


class RenderEngine:
    """
    协调 DOCX/PDF 渲染与格式转换的统一入口。
    """

    def __init__(
        self,
        *,
        template_root: Path | None = None,
        command_runner: CommandRunner | None = None,
        repository: TemplateRepository = template_repository,
    ) -> None:
        template_root = template_root or settings.template_root
        command_runner = command_runner or CommandRunner()

        self.docx_renderer = DocxRenderService(template_root=template_root)
        self.pdf_renderer = PdfRenderService(command_runner=command_runner)
        self.conversion_pipeline = ConversionPipeline(command_runner=command_runner)
        self.template_root = template_root
        self.repository = repository

    def _resolve_template_path(self, metadata: TemplateMetadata) -> Path:
        template_dir = self.template_root / metadata.id
        return template_dir / metadata.entry

    @staticmethod
    def _normalise_formats(formats: Iterable[str] | None, metadata: TemplateMetadata) -> list[str]:
        if formats:
            return list(dict.fromkeys([fmt.lower() for fmt in formats]))
        if metadata.options and metadata.options.allowed_outputs:
            return [fmt.lower() for fmt in metadata.options.allowed_outputs]
        return ["docx"]

    @staticmethod
    def _parse_pdf_options(options: dict[str, Any] | None) -> PdfRenderOptions:
        options = options or {}
        pdf_options = options.get("pdf") if isinstance(options, dict) else {}
        if not isinstance(pdf_options, dict):
            pdf_options = {}

        flatten = bool(pdf_options.get("flatten") or pdf_options.get("allow_flatten"))
        pdfa = bool(pdf_options.get("pdfa") or pdf_options.get("allow_pdfa"))
        password = pdf_options.get("password")
        if password is not None:
            password = str(password)

        return PdfRenderOptions(flatten=flatten, pdfa=pdfa, password=password)

    def render(
        self,
        request: RenderRequest,
    ) -> list[RenderOutcome]:
        metadata = self.repository.get_template(request.template_id)
        template_path = self._resolve_template_path(metadata)

        workdir = Path(tempfile.mkdtemp(prefix=f"render-{metadata.id}-"))
        logger.debug("使用工作目录: {workdir}", workdir=workdir.as_posix())

        try:
            if template_path.suffix.lower() == ".docx":
                docx_output = workdir / f"{metadata.id}.docx"
                self.docx_renderer.render(metadata, request.data, output_path=docx_output)
                target_formats = self._normalise_formats(request.formats, metadata)
                conversions = self.conversion_pipeline.convert_docx(
                    docx_output,
                    target_formats,
                    workdir=workdir,
                )
                return [self._persist_result(result) for result in conversions]

            if template_path.suffix.lower() == ".pdf":
                if request.formats and any(fmt.lower() != "pdf" for fmt in request.formats):
                    raise ValueError("PDF 模板目前仅支持导出为 PDF 格式")

                pdf_output = workdir / f"{metadata.id}.pdf"
                options = self._parse_pdf_options(request.options)
                self.pdf_renderer.render(
                    template_path,
                    request.data,
                    output_path=pdf_output,
                    options=options,
                )
                return [self._persist_output("pdf", pdf_output)]

            raise ValueError(f"暂不支持的模板类型: {template_path.suffix}")
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    @staticmethod
    def _persist_result(result: ConversionResult) -> RenderOutcome:
        return RenderEngine._persist_output(result.format, result.output_path)

    @staticmethod
    def _persist_output(fmt: str, source: Path) -> RenderOutcome:
        suffix = source.suffix if source.suffix else f".{fmt}"
        persistent_path = Path(tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name)
        shutil.copy2(source, persistent_path)
        return RenderOutcome(format=fmt, file_path=persistent_path)


render_engine = RenderEngine()


