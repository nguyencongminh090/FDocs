import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_result import AnalysisResult


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_document(self, document_id: uuid.UUID) -> AnalysisResult | None:
        result = await self.db.execute(
            select(AnalysisResult).where(AnalysisResult.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def upsert_field(self, document_id: uuid.UUID, **fields: Any) -> AnalysisResult:
        existing = await self.get_by_document(document_id)
        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        record = AnalysisResult(document_id=document_id, **fields)
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record
