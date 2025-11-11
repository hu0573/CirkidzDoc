from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from loguru import logger

from app.services.command_runner import CommandExecutionError, CommandRunner


class ConversionError(RuntimeError):
    """
    表示格式转换失败。
    """


@dataclass(slots=True)
class ConversionResult:
    format: str
    output_path: Path


class ConversionPipeline:
    """
    文档格式转换流水线，负责协调 LibreOffice / Pandoc 等工具。
    """

    DOCX_OUTPUTS = {"docx", "pdf", "html", "rtf", "tex", "markdown", "md"}

    def __init__(self, *, command_runner: CommandRunner | None = None) -> None:
        self.command_runner = command_runner or CommandRunner()

    @staticmethod
    def normalise_format(target_format: str) -> str:
        fmt = target_format.lower()
        if fmt == "md":
            return "markdown"
        return fmt

    def _ensure_supported(self, target_format: str) -> None:
        fmt = self.normalise_format(target_format)
        if fmt not in self.DOCX_OUTPUTS:
            raise ConversionError(f"暂不支持的输出格式: {target_format}")

    def convert_docx(
        self,
        source_docx: Path,
        target_formats: Iterable[str],
        *,
        workdir: Path,
    ) -> list[ConversionResult]:
        if not source_docx.exists():
            raise FileNotFoundError(f"DOCX 文件不存在: {source_docx}")

        workdir.mkdir(parents=True, exist_ok=True)

        results: list[ConversionResult] = []
        requested_formats = {self.normalise_format(fmt): fmt for fmt in target_formats}
        for fmt, original_fmt in requested_formats.items():
            self._ensure_supported(fmt)

            if fmt == "docx":
                output_path = workdir / f"{source_docx.stem}.docx"
                if output_path.resolve() != source_docx.resolve():
                    shutil.copyfile(source_docx, output_path)
                else:
                    output_path = source_docx
                results.append(ConversionResult(format=original_fmt, output_path=output_path))
                continue

            if fmt == "pdf":
                results.append(
                    ConversionResult(
                        format=original_fmt,
                        output_path=self._convert_docx_to_pdf(source_docx, workdir),
                    )
                )
                continue

            results.append(
                ConversionResult(
                    format=original_fmt,
                    output_path=self._convert_docx_with_pandoc(source_docx, fmt, workdir),
                )
            )

        return results

    def _convert_docx_to_pdf(self, source_docx: Path, workdir: Path) -> Path:
        if not CommandRunner.is_available("libreoffice"):
            raise ConversionError("未检测到 libreoffice，请安装后再试。")

        output_path = workdir / f"{source_docx.stem}.pdf"
        try:
            self.command_runner.run(
                (
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "pdf:writer_pdf_Export",
                    source_docx.as_posix(),
                    "--outdir",
                    workdir.as_posix(),
                ),
                timeout=240,
            )
        except CommandExecutionError as exc:
            raise ConversionError(f"LibreOffice 转换 PDF 失败: {exc}") from exc

        if not output_path.exists():
            raise ConversionError("LibreOffice 未生成 PDF 文件。")

        logger.info("DOCX -> PDF 转换完成: {path}", path=output_path.as_posix())
        return output_path

    def _convert_docx_with_pandoc(self, source_docx: Path, fmt: str, workdir: Path) -> Path:
        if not CommandRunner.is_available("pandoc"):
            raise ConversionError("未检测到 pandoc，请安装后再试。")

        ext = "md" if fmt == "markdown" else fmt
        output_path = workdir / f"{source_docx.stem}.{ext}"
        target_writer = {
            "markdown": "gfm",
            "html": "html5",
            "rtf": "rtf",
            "tex": "latex",
        }[fmt]

        try:
            self.command_runner.run(
                (
                    "pandoc",
                    source_docx.as_posix(),
                    "-f",
                    "docx",
                    "-t",
                    target_writer,
                    "-o",
                    output_path.as_posix(),
                ),
                timeout=180,
            )
        except CommandExecutionError as exc:
            raise ConversionError(f"Pandoc 转换 {fmt} 失败: {exc}") from exc

        if not output_path.exists():
            raise ConversionError(f"Pandoc 未生成 {fmt} 文件。")

        logger.info("DOCX -> {fmt} 转换完成: {path}", fmt=fmt, path=output_path.as_posix())
        return output_path


