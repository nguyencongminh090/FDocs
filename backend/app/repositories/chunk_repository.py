import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, document_id: uuid.UUID, chunks: list[dict], commit: bool = True) -> None:
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
        if commit:
            await self.db.commit()
        else:
            await self.db.flush()

    async def get_similar(self, query_embedding: list[float], document_id: uuid.UUID, top_k: int = 5) -> list[Chunk]:
        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        return list(result.scalars().all())

    async def get_similar_lexical(self, query_text: str, document_id: uuid.UUID, top_k: int = 5) -> list[Chunk]:
        """Lexical (full-text) retrieval over chunk content, scoped to one document.
        'simple' config = tokenize without stemming — safe for mixed VI/EN academic text
        and ideal for exact term/acronym matches that dense embeddings miss. Computed
        on-the-fly (no tsvector column/index): per-doc chunk counts are small."""
        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .where(text("to_tsvector('simple', chunks.content) @@ plainto_tsquery('simple', :q)"))
            .order_by(text("ts_rank(to_tsvector('simple', chunks.content), plainto_tsquery('simple', :q)) DESC"))
            .limit(top_k)
            .params(q=query_text)
        )
        return list(result.scalars().all())

    async def get_doc_embedding_centroid(self, document_id: uuid.UUID) -> list[float] | None:
        result = await self.db.execute(
            text("SELECT avg(embedding) FROM chunks WHERE document_id = :doc_id"),
            {"doc_id": str(document_id)},
        )
        row = result.fetchone()
        if not row or row[0] is None:
            return None
        raw = row[0]
        return [float(x) for x in raw.strip("[]").split(",")]

    async def get_all_doc_centroids(self, user_id: uuid.UUID) -> list[dict]:
        """Return each document's centroid embedding (avg of all its chunks)."""
        result = await self.db.execute(
            text("""
                SELECT d.id::text AS id, d.title, d.word_count, d.file_type,
                       avg(c.embedding) AS centroid
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.user_id = :user_id
                GROUP BY d.id, d.title, d.word_count, d.file_type
            """),
            {"user_id": str(user_id)},
        )
        rows = []
        for row in result.fetchall():
            d = dict(row._mapping)
            if d["centroid"] is not None:
                raw = d["centroid"]
                d["centroid"] = [float(x) for x in raw.strip("[]").split(",")]
            rows.append(d)
        return rows

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
            {"embedding": "[" + ",".join(str(x) for x in query_embedding) + "]", "user_id": str(user_id), "exclude_id": str(exclude_doc_id), "top_k": top_k},
        )
        return [dict(row._mapping) for row in result.fetchall()]
