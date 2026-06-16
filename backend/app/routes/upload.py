import uuid

from fastapi import APIRouter, Depends

from app.middlewares.auth import get_current_user_id
from app.services import upload_job_service

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.get("/{job_id}/progress")
async def upload_progress(
    job_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    # JWT-authenticated (header, via fetch-based SSE on the client) and scoped to the
    # owning user, so one user cannot watch another's upload. No Gemini key needed here
    # — the background job already captured it.
    return upload_job_service.build_progress_response(job_id, user_id)
