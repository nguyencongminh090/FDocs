import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middlewares.auth import get_current_user_id, get_gemini_key, get_response_language
from app.schemas.analysis import (
    AnalysisResultResponse,
    KGResponse,
    KeywordsResponse,
    RelatedDocResponse,
    RelevanceInput,
    RelevanceResponse,
    SummaryResponse,
    TimePlanInput,
    TimePlanResponse,
)
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/documents/{doc_id}", tags=["analysis"])


@router.get("/analysis", response_model=AnalysisResultResponse | None)
async def get_analysis(doc_id: uuid.UUID, user_id: uuid.UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await AnalysisService(db).get_analysis(doc_id, user_id)


@router.post("/analyze/summary", response_model=SummaryResponse)
async def summarize(
    doc_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
    lang: str | None = Depends(get_response_language),
    db: AsyncSession = Depends(get_db),
):
    summary = await AnalysisService(db).summarize(doc_id, user_id, gemini_key, lang=lang)
    return SummaryResponse(summary=summary)


@router.post("/analyze/keywords", response_model=KeywordsResponse)
async def extract_keywords(
    doc_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
    db: AsyncSession = Depends(get_db),
):
    keywords = await AnalysisService(db).extract_keywords(doc_id, user_id, gemini_key)
    return KeywordsResponse(keywords=keywords)


@router.post("/analyze/relevance", response_model=RelevanceResponse)
async def score_relevance(
    doc_id: uuid.UUID,
    body: RelevanceInput,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
    lang: str | None = Depends(get_response_language),
    db: AsyncSession = Depends(get_db),
):
    result = await AnalysisService(db).score_relevance(doc_id, user_id, body.goal, body.keywords, body.topic, gemini_key, lang=lang)
    return RelevanceResponse(**result)


@router.post("/analyze/time-plan", response_model=TimePlanResponse)
async def generate_time_plan(
    doc_id: uuid.UUID,
    body: TimePlanInput,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
    db: AsyncSession = Depends(get_db),
):
    time_plan = await AnalysisService(db).generate_time_plan(doc_id, user_id, body.start_date, body.deadline, body.hours_per_day, gemini_key)
    return TimePlanResponse(time_plan=time_plan)


@router.post("/analyze/knowledge-graph", response_model=KGResponse)
async def generate_kg(
    doc_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
    db: AsyncSession = Depends(get_db),
):
    kg = await AnalysisService(db).generate_kg(doc_id, user_id, gemini_key)
    return KGResponse(kg=kg)


@router.get("/related", response_model=list[RelatedDocResponse])
async def get_related(
    doc_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    gemini_key: str = Depends(get_gemini_key),
    db: AsyncSession = Depends(get_db),
):
    return await AnalysisService(db).get_related_docs(doc_id, user_id, gemini_key)
