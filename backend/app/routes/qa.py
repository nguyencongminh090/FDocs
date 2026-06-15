import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middlewares.auth import get_current_user_id, get_gemini_key
from app.schemas.qa import QARequest, QAResponse
from app.services.qa_service import QAService

router = APIRouter(prefix="/api/documents/{doc_id}/qa", tags=["qa"])


@router.post("", response_model=QAResponse)
async def ask(
    doc_id: uuid.UUID,
    body: QARequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
    db: AsyncSession = Depends(get_db),
):
    return await QAService(db).ask(doc_id, user_id, body.question, gemini_key)


@router.get("", response_model=list[QAResponse])
async def get_history(
    doc_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await QAService(db).get_history(doc_id, user_id)
