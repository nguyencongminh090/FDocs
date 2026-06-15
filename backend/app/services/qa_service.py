import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.qa_repository import QARepository
from app.services import gemini_service


class QAService:
    def __init__(self, db: AsyncSession):
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.qa_repo = QARepository(db)

    async def ask(self, doc_id: uuid.UUID, user_id: uuid.UUID, question: str, gemini_key: str):
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        query_embedding = await gemini_service.embed_query(question, gemini_key)
        similar_chunks = await self.chunk_repo.get_similar(query_embedding, doc_id, top_k=5)

        context = [c.content for c in similar_chunks]
        answer = await gemini_service.answer_question(question, context, gemini_key)

        sources = [
            {"chunk_id": str(c.id), "chunk_index": c.chunk_index, "excerpt": c.content[:200]}
            for c in similar_chunks
        ]
        return await self.qa_repo.create(doc_id, question, answer, sources)

    async def get_history(self, doc_id: uuid.UUID, user_id: uuid.UUID):
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return await self.qa_repo.get_by_document(doc_id)
