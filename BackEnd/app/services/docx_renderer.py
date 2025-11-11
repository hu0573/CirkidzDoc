from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from docx.shared import Cm, Inches, Mm, Pt
from docxtpl import DocxTemplate, InlineImage
from loguru import logger

from app.models.templates import TemplateMetadata


@dataclass(slots=True)
class ImageSpec:
    path: Path
    width: float | None = None
    height: float | None = None
    unit: str = "mm"
    description: str | None = None


def _resolve_length(value: float, unit: str) -> Mm | Inches | Cm | Pt:
    unit_map = {
        "mm": Mm,
        "millimeter": Mm,
        "millimetre": Mm,
        "cm": Cm,
        "centimeter": Cm,
        "inch": Inches,
        "inches": Inches,
        "pt": Pt,
        "point": Pt,
    }
    converter = unit_map.get(unit.lower())
    if converter is None:
        raise ValueError(f"Unsupported image unit: {unit}")
    return converter(value)


def _parse_image(value: Any, template_dir: Path) -> ImageSpec | None:
    if isinstance(value, ImageSpec):
        return value
    if not isinstance(value, dict):
        return None
    if value.get("__type") != "image":
        return None

    raw_path = value.get("path")
    if raw_path is None:
        raise ValueError("Image specification is missing the path field.")

    image_path = Path(raw_path)
    if not image_path.is_absolute():
        image_path = (template_dir / image_path).resolve()

    width = value.get("width") or value.get("width_mm") or value.get("width_cm") or value.get("width_in")
    height = value.get("height") or value.get("height_mm") or value.get("height_cm") or value.get("height_in")
    unit = value.get("unit") or ("cm" if value.get("width_cm") or value.get("height_cm") else None)
    if unit is None:
        if value.get("width_in") or value.get("height_in"):
            unit = "inch"
        elif value.get("width_mm") or value.get("height_mm"):
            unit = "mm"
        else:
            unit = "mm"

    return ImageSpec(
        path=image_path,
        width=float(width) if width is not None else None,
        height=float(height) if height is not None else None,
        unit=unit,
        description=value.get("description"),
    )


def _normalise_scalar(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class DocxRenderService:
    """
    DOCX rendering service built on top of docxtpl.
    """

    def __init__(self, template_root: Path) -> None:
        self.template_root = template_root

    def render(
        self,
        metadata: TemplateMetadata,
        data: dict[str, Any],
        *,
        output_path: Path,
    ) -> Path:
        template_dir = self.template_root / metadata.id
        template_path = template_dir / metadata.entry

        if not template_path.exists():
            raise FileNotFoundError(f"Template file does not exist: {template_path}")

        logger.info("Rendering DOCX template {template_id}", template_id=metadata.id)
        tpl = DocxTemplate(template_path)

        context: dict[str, Any] = {}
        for key, raw_value in data.items():
            image_spec = _parse_image(raw_value, template_dir)
            if image_spec:
                if not image_spec.path.exists():
                    raise FileNotFoundError(f"Image file does not exist: {image_spec.path}")
                mimetype, _ = mimetypes.guess_type(str(image_spec.path))
                if mimetype is None or not mimetype.startswith("image/"):
                    raise ValueError(f"Invalid image file type: {image_spec.path}")

                inline_kwargs: dict[str, Any] = {}
                if image_spec.width is not None:
                    inline_kwargs["width"] = _resolve_length(image_spec.width, image_spec.unit)
                if image_spec.height is not None:
                    inline_kwargs["height"] = _resolve_length(image_spec.height, image_spec.unit)

                context[key] = InlineImage(tpl, image_spec.path.as_posix(), **inline_kwargs)
                continue

            context[key] = _normalise_scalar(raw_value)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        tpl.render(context)
        tpl.save(output_path.as_posix())

        logger.info("DOCX render complete. Output file: {output}", output=output_path.as_posix())
        return output_path


