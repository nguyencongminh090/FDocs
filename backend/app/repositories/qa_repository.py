import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.qa_history import QAHistory


class QARepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, document_id: uuid.UUID, question: str, answer: str, sources: list | None) -> QAHistory:
        record = QAHistory(document_id=document_id, question=question, answer=answer, sources=sources)
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_by_document(self, document_id: uuid.UUID) -> list[QAHistory]:
        result = await self.db.execute(
            select(QAHistory).where(QAHistory.document_id == document_id).order_by(QAHistory.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete_by_document(self, document_id: uuid.UUID) -> None:
        await self.db.execute(delete(QAHistory).where(QAHistory.document_id == document_id))
        await self.db.commit()
