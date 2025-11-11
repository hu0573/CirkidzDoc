from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


FieldType = Literal["string", "number", "boolean", "date", "enum", "file", "textarea", "richtext"]


class FieldSchema(BaseModel):
    name: str
    type: FieldType


class TemplateMetadata(BaseModel):
    id: str
    name: str
    description: str | None = None
    entry: str
    fields: list[FieldSchema] = Field(default_factory=list)


class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    entry: str
    field_count: int = 0

    @classmethod
    def from_metadata(cls, metadata: TemplateMetadata) -> "TemplateSummary":
        return cls(
            id=metadata.id,
            name=metadata.name,
            description=metadata.description,
            entry=metadata.entry,
            field_count=len(metadata.fields),
        )


class TemplateDetail(BaseModel):
    template: TemplateMetadata


class TemplateCreationResponse(BaseModel):
    template: TemplateMetadata
    metadata_path: str
    message: str


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

