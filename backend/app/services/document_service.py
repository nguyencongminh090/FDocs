import re
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services import gemini_service


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

    async def create_document(self, user_id: uuid.UUID, data: dict, gemini_key: str):
        sections = detect_sections(data["extracted_text"])
        doc = await self.doc_repo.create(
            user_id=user_id,
            title=data["title"],
            file_type=data["file_type"],
            extracted_text=data["extracted_text"],
            word_count=data.get("word_count"),
            page_count=data.get("page_count"),
            sections=sections,
        )
        raw_chunks = gemini_service.chunk_text(data["extracted_text"])
        embeddings = await gemini_service.embed_texts(raw_chunks, gemini_key)
        chunk_records = [
            {"content": content, "embedding": emb, "chunk_index": idx}
            for idx, (content, emb) in enumerate(zip(raw_chunks, embeddings))
        ]
        await self.chunk_repo.bulk_create(doc.id, chunk_records)
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
