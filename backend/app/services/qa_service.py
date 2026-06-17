import json
import logging
import uuid

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.qa_repository import QARepository
from app.services import gemini_service

logger = logging.getLogger(__name__)


class QAService:
    def __init__(self, db: AsyncSession):
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.qa_repo = QARepository(db)

    async def ask(self, doc_id: uuid.UUID, user_id: uuid.UUID, question: str, gemini_key: str, lang: str | None = None):
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        query_embedding = await gemini_service.embed_query(question, gemini_key)
        similar_chunks = await self.chunk_repo.get_similar(query_embedding, doc_id, top_k=5)

        context = [c.content for c in similar_chunks]
        answer = await gemini_service.answer_question(question, context, gemini_key, lang=lang)

        sources = [
            {"chunk_id": str(c.id), "chunk_index": c.chunk_index, "excerpt": c.content[:200]}
            for c in similar_chunks
        ]
        return await self.qa_repo.create(doc_id, question, answer, sources)

    async def ask_stream_response(
        self, doc_id: uuid.UUID, user_id: uuid.UUID, question: str, gemini_key: str, lang: str | None = None
    ) -> StreamingResponse:
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        query_embedding = await gemini_service.embed_query(question, gemini_key)
        similar_chunks = await self.chunk_repo.get_similar(query_embedding, doc_id, top_k=5)

        context = [c.content for c in similar_chunks]
        sources = [
            {"chunk_id": str(c.id), "chunk_index": c.chunk_index, "excerpt": c.content[:200]}
            for c in similar_chunks
        ]

        qa_repo = self.qa_repo

        async def event_generator():
            full_answer_parts: list[str] = []
            completed = False
            try:
                async for token in gemini_service.answer_question_stream(question, context, gemini_key, lang=lang):
                    full_answer_parts.append(token)
                    # JSON-encode each token so newlines and special chars are safe in SSE data
                    yield f"data: {json.dumps(token)}\n\n"
                completed = True
                yield "data: [DONE]\n\n"
            except gemini_service.GeminiQuotaError as e:
                # HTTP 200 is already committed, so the only way to signal the client
                # is an in-band error frame (not an HTTP status).
                yield f"data: {json.dumps({'error': 'quota', 'detail': str(e)})}\n\n"
            except gemini_service.GeminiServiceError as e:
                yield f"data: {json.dumps({'error': 'service', 'detail': str(e)})}\n\n"
            except Exception as e:
                logger.error("Lỗi không mong đợi khi stream Q&A doc=%s: %s", doc_id, e, exc_info=True)
                yield f"data: {json.dumps({'error': 'server', 'detail': 'Lỗi máy chủ khi trả lời.'})}\n\n"
            finally:
                # Persist only a fully-streamed answer — never save a truncated/failed one.
                # [DONE] is already flushed by now, so a save failure cannot reach the
                # client; log it instead of letting it bubble as an ASGI error.
                if completed and full_answer_parts:
                    try:
                        await qa_repo.create(doc_id, question, "".join(full_answer_parts), sources)
                    except Exception as e:
                        logger.error("Không lưu được câu trả lời Q&A doc=%s sau khi stream xong: %s", doc_id, e, exc_info=True)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    async def get_history(self, doc_id: uuid.UUID, user_id: uuid.UUID):
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return await self.qa_repo.get_by_document(doc_id)
