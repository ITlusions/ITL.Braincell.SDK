"""Core schemas — shared types only.
Entity schemas have moved to itl_braincell_sdk/cells/<name>/schema.py.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


def schema_to_db_kwargs(schema: BaseModel) -> dict:
    """Convert a Create schema to DB model kwargs.

    Excludes None values so that columns with server-side defaults
    (e.g. created_at = func.now()) use those defaults when the caller
    did not supply an explicit value.  When a value IS supplied (e.g.
    created_at from an import/replay), it is passed through so the
    original timestamp is preserved.
    """
    return schema.model_dump(exclude_none=True)


class SearchQuery(BaseModel):
    query: str
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


class SearchResult(BaseModel):
    id: UUID
    type: str  # 'conversation', 'decision', 'note', etc.
    title: str
    content: str
    similarity_score: Optional[float] = None
    meta_data: dict
