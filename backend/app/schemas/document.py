import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class DocumentCreateRequest(BaseModel):
    title: str
    file_type: str
    word_count: int | None = None
    page_count: int | None = None
    extracted_text: str
    sections: Any | None = None

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        if v not in ("pdf", "docx"):
            raise ValueError("file_type must be 'pdf' or 'docx'")
        return v

    @field_validator("extracted_text")
    @classmethod
    def validate_extracted_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("extracted_text cannot be empty")
        return v


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    file_type: str
    word_count: int | None
    page_count: int | None
    sections: Any | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    extracted_text: str
