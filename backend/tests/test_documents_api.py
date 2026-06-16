"""Test cho /api/documents — unit (detect_sections) + integration (CRUD, guards, validation)."""
import uuid
from datetime import datetime, timezone

import pytest

from app.database import get_db
from app.main import app
from app.middlewares.auth import get_current_user_id, get_gemini_key
from app.services import document_service
from app.services.document_service import detect_sections
from tests.conftest import TEST_GEMINI_KEY, TEST_USER_ID, _fake_get_db

DOC_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


class TestDetectSections:
    def test_markdown_headings(self):
        text = "# Chương 1\nNội dung\n## Phần A\nThêm nội dung"
        sections = detect_sections(text)
        assert sections is not None
        assert len(sections) == 2
        assert sections[0]["index"] == 0

    def test_vietnamese_chapter_heading(self):
        sections = detect_sections("Chương 1 Giới thiệu\nnội dung dài ở đây")
        assert sections is not None
        assert len(sections) == 1

    def test_numbered_heading(self):
        sections = detect_sections("1. Tổng quan về đại số\nnội dung")
        assert sections is not None

    def test_no_heading_returns_none(self):
        assert detect_sections("chỉ là một đoạn văn bản phẳng không có tiêu đề nào cả") is None


class _Doc:
    def __init__(self, user_id):
        self.id = DOC_ID
        self.user_id = user_id
        self.title = "Test Doc"
        self.file_type = "pdf"
        self.word_count = 100
        self.page_count = 5
        self.sections = None
        self.extracted_text = "Nội dung tài liệu."
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


@pytest.fixture
def mock_docs(monkeypatch):
    def setup(owner_id=TEST_USER_ID):
        doc = _Doc(owner_id)

        class FakeDocRepo:
            def __init__(self, db=None):
                pass

            async def create(self, **kwargs):
                return doc

            async def get_by_id(self, doc_id):
                return doc

            async def get_by_user(self, user_id):
                return [doc]

            async def delete(self, d):
                return None

        class FakeChunkRepo:
            def __init__(self, db=None):
                pass

            async def bulk_create(self, doc_id, chunks, commit=True):
                return None

        monkeypatch.setattr(document_service, "DocumentRepository", FakeDocRepo)
        monkeypatch.setattr(document_service, "ChunkRepository", FakeChunkRepo)
        monkeypatch.setattr(document_service.gemini_service, "chunk_text", lambda t: ["c1"])

        async def fake_embed(texts, key, progress_callback=None):
            if progress_callback:
                progress_callback(len(texts), len(texts))
            return [[0.1, 0.2]]

        monkeypatch.setattr(document_service.gemini_service, "embed_texts", fake_embed)
        return doc

    yield setup
    app.dependency_overrides.clear()


def _authed():
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    app.dependency_overrides[get_gemini_key] = lambda: TEST_GEMINI_KEY
    app.dependency_overrides[get_db] = _fake_get_db


class TestDocumentsCRUD:
    async def test_create_document_202_returns_job_id(self, client, mock_docs, monkeypatch):
        from app.services import upload_job_service

        captured = {}

        def fake_enqueue(user_id, data, gemini_key):
            captured["data"] = data
            captured["gemini_key"] = gemini_key
            return "job-abc"

        monkeypatch.setattr(upload_job_service, "enqueue", fake_enqueue)
        mock_docs()
        _authed()
        resp = await client.post(
            "/api/documents",
            json={"title": "Test Doc", "file_type": "pdf", "extracted_text": "Nội dung tài liệu."},
        )
        assert resp.status_code == 202
        assert resp.json() == {"job_id": "job-abc"}
        # The BYOK key reaches the job layer (it is never persisted there).
        assert captured["gemini_key"] == TEST_GEMINI_KEY
        assert captured["data"]["title"] == "Test Doc"

    async def test_list_documents(self, client, mock_docs):
        mock_docs()
        _authed()
        resp = await client.get("/api/documents")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_document_detail_includes_text(self, client, mock_docs):
        mock_docs()
        _authed()
        resp = await client.get(f"/api/documents/{DOC_ID}")
        assert resp.status_code == 200
        assert "extracted_text" in resp.json()

    async def test_get_document_not_owned_404(self, client, mock_docs):
        mock_docs(owner_id=uuid.uuid4())
        _authed()
        resp = await client.get(f"/api/documents/{DOC_ID}")
        assert resp.status_code == 404

    async def test_delete_document_204(self, client, mock_docs):
        mock_docs()
        _authed()
        resp = await client.delete(f"/api/documents/{DOC_ID}")
        assert resp.status_code == 204


class TestDocumentValidation:
    async def test_invalid_file_type_422(self, client, mock_docs):
        mock_docs()
        _authed()
        resp = await client.post(
            "/api/documents",
            json={"title": "X", "file_type": "txt", "extracted_text": "nội dung"},
        )
        assert resp.status_code == 422

    async def test_empty_extracted_text_422(self, client, mock_docs):
        mock_docs()
        _authed()
        resp = await client.post(
            "/api/documents",
            json={"title": "X", "file_type": "pdf", "extracted_text": "   "},
        )
        assert resp.status_code == 422

    async def test_create_requires_auth_403(self, client, mock_docs):
        mock_docs()
        app.dependency_overrides[get_db] = _fake_get_db
        resp = await client.post(
            "/api/documents",
            json={"title": "X", "file_type": "pdf", "extracted_text": "nội dung"},
        )
        assert resp.status_code == 403

    async def test_null_bytes_stripped_and_create_succeeds(self, client, mock_docs, monkeypatch):
        """PDF text with null bytes must not reach DB — validator strips them (regression: asyncpg.CharacterNotInRepertoireError)."""
        from app.services import upload_job_service

        captured = {}

        def fake_enqueue(user_id, data, gemini_key):
            captured["text"] = data["extracted_text"]
            return "job-xyz"

        monkeypatch.setattr(upload_job_service, "enqueue", fake_enqueue)
        mock_docs()
        _authed()
        null = chr(0)
        text_with_nulls = f"Noi dung{null}co null{null}byte"
        resp = await client.post(
            "/api/documents",
            json={"title": "PDF null byte", "file_type": "pdf", "extracted_text": text_with_nulls},
        )
        assert resp.status_code == 202
        assert null not in captured["text"]

    async def test_only_null_bytes_is_empty_422(self, client, mock_docs):
        """Text consisting only of null bytes is treated as empty after stripping."""
        mock_docs()
        _authed()
        null = chr(0)
        resp = await client.post(
            "/api/documents",
            json={"title": "X", "file_type": "pdf", "extracted_text": null * 5},
        )
        assert resp.status_code == 422


class TestDocumentTransaction:
    """Regression: embedding ran AFTER the doc was committed, so a failed embedding
    left an orphaned document with no chunks. Embedding now runs first and nothing is
    persisted if it fails."""

    def _wire(self, monkeypatch, embed_fn):
        from app.services import document_service as ds

        state = {"doc_created": False, "chunks_created": False}

        class FakeDocRepo:
            def __init__(self, db=None):
                pass

            async def create(self, **kwargs):
                state["doc_created"] = True
                return _Doc(TEST_USER_ID)

        class FakeChunkRepo:
            def __init__(self, db=None):
                pass

            async def bulk_create(self, doc_id, chunks, commit=True):
                state["chunks_created"] = True

        monkeypatch.setattr(ds, "DocumentRepository", FakeDocRepo)
        monkeypatch.setattr(ds, "ChunkRepository", FakeChunkRepo)
        monkeypatch.setattr(ds.gemini_service, "chunk_text", lambda t: ["c1"])
        monkeypatch.setattr(ds.gemini_service, "embed_texts", embed_fn)
        return state

    async def test_embed_quota_error_raises_without_persisting(self, monkeypatch):
        from app.services.document_service import DocumentService
        from app.services.gemini_service import GeminiQuotaError

        async def quota_boom(texts, key, progress_callback=None):
            raise GeminiQuotaError("Đã vượt giới hạn quota Gemini API.")

        state = self._wire(monkeypatch, quota_boom)
        with pytest.raises(GeminiQuotaError):
            await DocumentService(None).create_document(
                TEST_USER_ID,
                {"title": "X", "file_type": "pdf", "extracted_text": "nội dung"},
                TEST_GEMINI_KEY,
            )
        assert state["doc_created"] is False
        assert state["chunks_created"] is False

    async def test_embed_generic_error_raises_without_persisting(self, monkeypatch):
        from app.services.document_service import DocumentService
        from app.services.gemini_service import GeminiServiceError

        async def generic_boom(texts, key, progress_callback=None):
            raise GeminiServiceError("Không thể tạo embedding từ Gemini API.")

        state = self._wire(monkeypatch, generic_boom)
        with pytest.raises(GeminiServiceError):
            await DocumentService(None).create_document(
                TEST_USER_ID,
                {"title": "X", "file_type": "pdf", "extracted_text": "nội dung"},
                TEST_GEMINI_KEY,
            )
        assert state["doc_created"] is False
        assert state["chunks_created"] is False
