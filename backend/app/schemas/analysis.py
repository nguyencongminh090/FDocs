import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RelevanceInput(BaseModel):
    goal: str
    keywords: list[str] = Field(default_factory=list)
    topic: str


class TimePlanInput(BaseModel):
    start_date: str
    deadline: str
    hours_per_day: float = Field(gt=0)


class AnalysisResultResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    summary: str | None
    keywords: list[str] | None
    relevance_score: float | None
    relevance_input: dict | None
    time_plan: list | None
    time_plan_input: dict | None
    kg: dict | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class SummaryResponse(BaseModel):
    summary: str


class KeywordsResponse(BaseModel):
    keywords: list[str]


class RelevanceResponse(BaseModel):
    relevance_score: float
    explanation: str


class TimePlanResponse(BaseModel):
    time_plan: list[Any]


class KGResponse(BaseModel):
    kg: dict


class RelatedDocResponse(BaseModel):
    id: uuid.UUID
    title: str
    file_type: str
    similarity_score: float
    created_at: datetime
