import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator

# Upper bound on extracted text (~160k words / ~600 pages). Guards against abusive
# payloads and unbounded chunk/embedding fan-out per the security rule on payload size.
MAX_EXTRACTED_TEXT_CHARS = 1_000_000


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
        # PostgreSQL UTF-8 rejects \x00; strip before any DB or embedding operation.
        v = v.replace("\x00", "")
        if not v.strip():
            raise ValueError("extracted_text cannot be empty")
        if len(v) > MAX_EXTRACTED_TEXT_CHARS:
            raise ValueError(f"extracted_text vượt giới hạn {MAX_EXTRACTED_TEXT_CHARS} ký tự")
        return v


class DocumentJobResponse(BaseModel):
    """Returned by POST /api/documents (202): the upload is processed asynchronously,
    so the client gets a job handle to watch via GET /api/upload/{job_id}/progress."""
    job_id: str


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
