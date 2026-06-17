import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services import gemini_service


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.doc_repo = DocumentRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.chunk_repo = ChunkRepository(db)

    async def _require_doc(self, doc_id: uuid.UUID, user_id: uuid.UUID):
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return doc

    async def get_analysis(self, doc_id: uuid.UUID, user_id: uuid.UUID):
        await self._require_doc(doc_id, user_id)
        return await self.analysis_repo.get_by_document(doc_id)

    async def summarize(self, doc_id: uuid.UUID, user_id: uuid.UUID, gemini_key: str, lang: str | None = None) -> str:
        doc = await self._require_doc(doc_id, user_id)
        summary = await gemini_service.generate_summary(doc.extracted_text, gemini_key, lang=lang)
        await self.analysis_repo.upsert_field(doc_id, summary=summary)
        return summary

    async def extract_keywords(self, doc_id: uuid.UUID, user_id: uuid.UUID, gemini_key: str) -> list[str]:
        doc = await self._require_doc(doc_id, user_id)
        keywords = await gemini_service.extract_keywords(doc.extracted_text, gemini_key)
        await self.analysis_repo.upsert_field(doc_id, keywords=keywords)
        return keywords

    async def score_relevance(self, doc_id: uuid.UUID, user_id: uuid.UUID, goal: str, keywords: list[str], topic: str, gemini_key: str, lang: str | None = None) -> dict:
        doc = await self._require_doc(doc_id, user_id)
        result = await gemini_service.score_relevance(doc.extracted_text, goal, keywords, topic, gemini_key, lang=lang)
        await self.analysis_repo.upsert_field(
            doc_id,
            relevance_score=result["relevance_score"],
            relevance_input={"goal": goal, "keywords": keywords, "topic": topic},
        )
        return result

    async def generate_time_plan(self, doc_id: uuid.UUID, user_id: uuid.UUID, start_date: str, deadline: str, hours_per_day: float, gemini_key: str) -> list:
        doc = await self._require_doc(doc_id, user_id)
        time_plan = await gemini_service.generate_time_plan(
            sections=doc.sections,
            word_count=doc.word_count or 0,
            start_date=start_date,
            deadline=deadline,
            hours_per_day=hours_per_day,
            api_key=gemini_key,
        )
        await self.analysis_repo.upsert_field(
            doc_id,
            time_plan=time_plan,
            time_plan_input={"start_date": start_date, "deadline": deadline, "hours_per_day": hours_per_day},
        )
        return time_plan

    async def generate_kg(self, doc_id: uuid.UUID, user_id: uuid.UUID, gemini_key: str) -> dict:
        doc = await self._require_doc(doc_id, user_id)
        kg = await gemini_service.generate_knowledge_graph(doc.extracted_text, gemini_key)
        await self.analysis_repo.upsert_field(doc_id, kg=kg)
        return kg

    async def get_related_docs(self, doc_id: uuid.UUID, user_id: uuid.UUID, gemini_key: str) -> list[dict]:
        await self._require_doc(doc_id, user_id)
        centroid = await self.chunk_repo.get_doc_embedding_centroid(doc_id)
        if centroid is None:
            return []
        return await self.chunk_repo.get_similar_docs(centroid, user_id, exclude_doc_id=doc_id)
