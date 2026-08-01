"""CodeSnippet Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CodeSnippetCreate(BaseModel):
    title: str
    code_content: str
    language: str | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    description: str | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class CodeSnippetResponse(BaseModel):
    id: UUID
    title: str
    code_content: str
    language: str | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    description: str | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
