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

            async def bulk_create(self, doc_id, chunks):
                return None

        monkeypatch.setattr(document_service, "DocumentRepository", FakeDocRepo)
        monkeypatch.setattr(document_service, "ChunkRepository", FakeChunkRepo)
        monkeypatch.setattr(document_service.gemini_service, "chunk_text", lambda t: ["c1"])

        async def fake_embed(texts, key):
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
    async def test_create_document_201(self, client, mock_docs):
        mock_docs()
        _authed()
        resp = await client.post(
            "/api/documents",
            json={"title": "Test Doc", "file_type": "pdf", "extracted_text": "Nội dung tài liệu."},
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Test Doc"

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
