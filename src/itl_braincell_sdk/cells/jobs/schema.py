"""Jobs cell schemas — Weaviate-only, no PostgreSQL model"""
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class JobInput(BaseModel):
    job_id: str
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    source: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    job_type: str | None = None
    seniority_level: str | None = None
    posted_date: str | None = None
    tags: list[str] | None = None


class BatchJobInput(BaseModel):
    jobs: list[JobInput]


class JobSearchQuery(BaseModel):
    query: str
    limit: int = 10
    source: str | None = None
    job_type: str | None = None
    location: str | None = None


class SearchResult(BaseModel):
    id: UUID
    type: str
    title: str
    content: str
    similarity_score: float
    metadata: dict[str, Any] | None = None
