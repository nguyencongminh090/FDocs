import re
import uuid
from collections.abc import Callable

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services import gemini_service

# Progress milestones (percent) reported via progress_cb during create_document.
# Embedding — the slow, batched Gemini step — owns the wide 5..90 band; the cheap
# local steps bracket it. The job layer sets 100 only after the row is committed.
_PROGRESS_CHUNKING = 5
_PROGRESS_EMBED_START = 5
_PROGRESS_EMBED_END = 90
_PROGRESS_SAVING = 95


def detect_sections(text: str) -> list[dict] | None:
    pattern = re.compile(
        r"^(#{1,3}\s+.+|CHAPTER\s+\d+.*|Chương\s+\d+.*|\d+\.\s+[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯẠẶ].+)$",
        re.MULTILINE | re.IGNORECASE,
    )
    headings = [m.group().strip() for m in pattern.finditer(text)]
    if not headings:
        return None
    return [{"title": h, "index": i} for i, h in enumerate(headings)]


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)

    async def create_document(
        self,
        user_id: uuid.UUID,
        data: dict,
        gemini_key: str,
        progress_cb: Callable[[str, int], None] | None = None,
    ):
        text = data["extracted_text"]
        # Embedding (external Gemini call) is the most failure-prone step, so run it
        # before any DB write. The document + chunks are then persisted in a single
        # transaction — a failed embedding leaves no orphaned document behind.
        if progress_cb is not None:
            progress_cb("chunking", _PROGRESS_CHUNKING)
        raw_chunks = gemini_service.chunk_text(text)

        embed_progress = None
        if progress_cb is not None:
            span = _PROGRESS_EMBED_END - _PROGRESS_EMBED_START

            def embed_progress(done: int, total: int) -> None:
                pct = _PROGRESS_EMBED_START + (span * done // total if total else span)
                progress_cb("embedding", pct)

        embeddings = await gemini_service.embed_texts(raw_chunks, gemini_key, progress_callback=embed_progress)

        if progress_cb is not None:
            progress_cb("saving", _PROGRESS_SAVING)
        sections = detect_sections(text)
        doc = await self.doc_repo.create(
            user_id=user_id,
            title=data["title"],
            file_type=data["file_type"],
            extracted_text=text,
            word_count=data.get("word_count"),
            page_count=data.get("page_count"),
            sections=sections,
            commit=False,
        )
        chunk_records = [
            {"content": content, "embedding": emb, "chunk_index": idx}
            for idx, (content, emb) in enumerate(zip(raw_chunks, embeddings))
        ]
        await self.chunk_repo.bulk_create(doc.id, chunk_records, commit=True)
        return doc

    async def get_document(self, doc_id: uuid.UUID, user_id: uuid.UUID):
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return doc

    async def list_documents(self, user_id: uuid.UUID):
        return await self.doc_repo.get_by_user(user_id)

    async def delete_document(self, doc_id: uuid.UUID, user_id: uuid.UUID) -> None:
        doc = await self.get_document(doc_id, user_id)
        await self.doc_repo.delete(doc)
