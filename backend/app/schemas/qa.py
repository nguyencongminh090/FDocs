import uuid
from datetime import datetime

from pydantic import BaseModel


class QARequest(BaseModel):
    question: str


class QAResponse(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    sources: list | None
    created_at: datetime

    model_config = {"from_attributes": True}
