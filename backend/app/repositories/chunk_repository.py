import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, document_id: uuid.UUID, chunks: list[dict]) -> None:
        objects = [
            Chunk(
                document_id=document_id,
                content=c["content"],
                embedding=c["embedding"],
                chunk_index=c["chunk_index"],
            )
            for c in chunks
        ]
        self.db.add_all(objects)
        await self.db.commit()

    async def get_similar(self, query_embedding: list[float], document_id: uuid.UUID, top_k: int = 5) -> list[Chunk]:
        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        return list(result.scalars().all())

    async def get_doc_embedding_centroid(self, document_id: uuid.UUID) -> list[float] | None:
        result = await self.db.execute(
            text("SELECT avg(embedding) FROM chunks WHERE document_id = :doc_id"),
            {"doc_id": str(document_id)},
        )
        row = result.fetchone()
        return list(row[0]) if row and row[0] is not None else None

    async def get_similar_docs(
        self,
        query_embedding: list[float],
        user_id: uuid.UUID,
        exclude_doc_id: uuid.UUID,
        top_k: int = 3,
    ) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT d.id, d.title, d.file_type, d.created_at,
                       1 - (avg(c.embedding) <=> CAST(:embedding AS vector)) AS similarity_score
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.user_id = :user_id AND d.id != :exclude_id
                GROUP BY d.id, d.title, d.file_type, d.created_at
                ORDER BY similarity_score DESC
                LIMIT :top_k
            """),
            {"embedding": query_embedding, "user_id": str(user_id), "exclude_id": str(exclude_doc_id), "top_k": top_k},
        )
        return [dict(row._mapping) for row in result.fetchall()]
