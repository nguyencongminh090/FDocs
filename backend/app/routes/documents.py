import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middlewares.auth import get_current_user_id, get_gemini_key
from app.schemas.document import DocumentCreateRequest, DocumentDetailResponse, DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def create_document(
    body: DocumentCreateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
    db: AsyncSession = Depends(get_db),
):
    doc = await DocumentService(db).create_document(user_id, body.model_dump(), gemini_key)
    return doc


@router.get("", response_model=list[DocumentResponse])
async def list_documents(user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await DocumentService(db).list_documents(user_id)


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: uuid.UUID, user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await DocumentService(db).get_document(doc_id, user_id)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: uuid.UUID, user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await DocumentService(db).delete_document(doc_id, user_id)
