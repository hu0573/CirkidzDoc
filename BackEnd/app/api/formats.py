from __future__ import annotations

from fastapi import APIRouter

from app.services.conversion_pipeline import ConversionPipeline

router = APIRouter()


@router.get("", summary="List supported output formats and advanced options")
def list_supported_formats() -> dict:
    """
    Return globally supported output formats and descriptions of advanced PDF options.
    """

    docx_formats = sorted(ConversionPipeline.DOCX_OUTPUTS)
    formats = [
        {
            "id": fmt,
            "label": fmt.upper(),
            "description": "Available export formats for DOCX templates"
            if fmt != "md"
            else "Markdown (GitHub flavored)",
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
                "description": "PDF rendering supports field flattening, PDF/A compliance, and password protection.",
            }
        },
    }


