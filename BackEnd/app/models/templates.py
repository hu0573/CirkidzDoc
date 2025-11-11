from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


FieldType = Literal["string", "number", "boolean", "date", "enum", "file", "textarea", "richtext"]


class ValidationRule(BaseModel):
    pattern: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    minimum: float | None = None
    maximum: float | None = None
    message: str | None = None


class FieldOption(BaseModel):
    label: str
    value: str


class FieldSchema(BaseModel):
    name: str
    label: str
    type: FieldType
    required: bool = False
    description: str | None = None
    placeholder: str | None = None
    default: Any = None
    options: list[FieldOption] | None = None
    validation: ValidationRule | None = None


class PdfOptionCapabilities(BaseModel):
    allow_flatten: bool = Field(default=True)
    allow_pdfa: bool = Field(default=True)
    allow_password: bool = Field(default=True)


class TemplateOptions(BaseModel):
    allowed_outputs: list[str] = Field(default_factory=list)
    pdf: PdfOptionCapabilities | None = None


class TemplateMetadata(BaseModel):
    id: str
    name: str
    description: str | None = None
    version: str | None = None
    entry: str
    preview: str | None = None
    fields: list[FieldSchema] = Field(default_factory=list)
    options: TemplateOptions | None = None


class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    version: str | None = None
    preview: str | None = None
    field_count: int = 0
    allowed_outputs: list[str] = Field(default_factory=list)

    @classmethod
    def from_metadata(cls, metadata: TemplateMetadata) -> "TemplateSummary":
        allowed_outputs: list[str] = []
        if metadata.options and metadata.options.allowed_outputs:
            allowed_outputs = metadata.options.allowed_outputs

        return cls(
            id=metadata.id,
            name=metadata.name,
            description=metadata.description,
            version=metadata.version,
            preview=metadata.preview,
            field_count=len(metadata.fields),
            allowed_outputs=allowed_outputs,
        )


class TemplateDetail(BaseModel):
    template: TemplateMetadata


class RenderRequest(BaseModel):
    template_id: str
    data: dict[str, Any]
    formats: list[str] = Field(default_factory=list)
    options: dict[str, Any] | None = None
    attachments: list[str] | None = None


class RenderResponse(BaseModel):
    task_id: str
    status: Literal["queued", "processing", "succeeded", "failed"]
    expires_at: datetime


class TaskResult(BaseModel):
    format: str
    download_url: str
    file_size: int | None = None
    checksum: str | None = None
    expires_at: datetime | None = None


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["queued", "processing", "succeeded", "failed"]
    progress: int = 0
    results: list[TaskResult] = Field(default_factory=list)
    error: str | None = None

