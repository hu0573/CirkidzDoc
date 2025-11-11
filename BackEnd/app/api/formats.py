from __future__ import annotations

from fastapi import APIRouter

from app.services.conversion_pipeline import ConversionPipeline

router = APIRouter()


@router.get("", summary="列出后端支持的输出格式与高级选项")
def list_supported_formats() -> dict:
    """
    返回全局支持的输出格式，以及 PDF 等高阶选项说明。
    """

    docx_formats = sorted(ConversionPipeline.DOCX_OUTPUTS)
    formats = [
        {
            "id": fmt,
            "label": fmt.upper(),
            "description": "DOCX 模板可导出的文件格式" if fmt != "md" else "Markdown (GitHub 风格)",
        }
        for fmt in docx_formats
    ]

    return {
        "formats": formats,
        "advanced_options": {
            "pdf": {
                "allow_flatten": True,
                "allow_pdfa": True,
                "allow_password": True,
                "description": "PDF 渲染支持扁平化、PDF/A 规范与密码保护。",
            }
        },
    }


