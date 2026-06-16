import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middlewares.auth import get_current_user_id, get_gemini_key
from app.schemas.document import (
    DocumentCreateRequest,
    DocumentDetailResponse,
    DocumentJobResponse,
    DocumentResponse,
)
from app.services import upload_job_service
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=DocumentJobResponse)
async def create_document(
    body: DocumentCreateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
):
    # Chunk + embed (100-170s for large docs) runs in the background to avoid a 504;
    # the client polls GET /api/upload/{job_id}/progress. The Gemini key is handed to
    # the in-memory job and never persisted (BYOK).
    job_id = upload_job_service.enqueue(user_id, body.model_dump(), gemini_key)
    return DocumentJobResponse(job_id=job_id)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await DocumentService(db).list_documents(user_id)


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: uuid.UUID, user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await DocumentService(db).get_document(doc_id, user_id)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: uuid.UUID, user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await DocumentService(db).delete_document(doc_id, user_id)
