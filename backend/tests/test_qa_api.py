"""Integration test cho /api/documents/{id}/qa — gồm SSE stream format + auth/key guards.

Repository + gemini_service được mock; verify HTTP behavior thật của route.
"""
import json
import uuid
from datetime import datetime, timezone

import pytest

from app.database import get_db
from app.main import app
from app.middlewares.auth import get_current_user_id, get_gemini_key
from app.services import gemini_service, qa_service
from tests.conftest import TEST_GEMINI_KEY, TEST_USER_ID, _fake_get_db

DOC_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


class _Doc:
    def __init__(self, user_id):
        self.id = DOC_ID
        self.user_id = user_id


class _Chunk:
    def __init__(self, idx, content, embedding=None):
        self.id = uuid.uuid4()
        self.chunk_index = idx
        self.content = content
        # MMR selection in qa_service reads .embedding; give each chunk a distinct vector.
        self.embedding = embedding if embedding is not None else [0.1 * (idx + 1), 0.2, 0.3]


class _QARow:
    def __init__(self, question, answer, sources):
        self.id = uuid.uuid4()
        self.question = question
        self.answer = answer
        self.sources = sources
        self.created_at = datetime.now(timezone.utc)


def _make_fakes(doc_owner_id):
    class FakeDocRepo:
        def __init__(self, db=None):
            pass

        async def get_by_id(self, doc_id):
            return _Doc(doc_owner_id)

    class FakeChunkRepo:
        def __init__(self, db=None):
            pass

        async def get_similar(self, embedding, doc_id, top_k=5):
            return [_Chunk(0, "Linear algebra is the study of vectors."), _Chunk(1, "Matrices represent transforms.")]

        async def get_similar_lexical(self, query_text, doc_id, top_k=5):
            return [_Chunk(2, "Eigenvalues describe scaling along eigenvectors.")]

    class FakeQARepo:
        def __init__(self, db=None):
            pass

        async def create(self, doc_id, question, answer, sources):
            return _QARow(question, answer, sources)

    return FakeDocRepo, FakeChunkRepo, FakeQARepo


@pytest.fixture
def mock_qa(monkeypatch):
    """Mock toàn bộ repo + gemini cho QAService. Trả về callable đặt owner của doc."""
    def setup(doc_owner_id=TEST_USER_ID):
        doc_repo, chunk_repo, qa_repo = _make_fakes(doc_owner_id)
        monkeypatch.setattr(qa_service, "DocumentRepository", doc_repo)
        monkeypatch.setattr(qa_service, "ChunkRepository", chunk_repo)
        monkeypatch.setattr(qa_service, "QARepository", qa_repo)

        async def fake_embed_query(question, key):
            return [0.1, 0.2, 0.3]

        async def fake_answer(question, context, key, **kw):
            return "Đây là câu trả lời."

        async def fake_stream(question, context, key, **kw):
            for tok in ["Đây ", "là ", "câu\ntrả lời."]:
                yield tok

        monkeypatch.setattr(qa_service.gemini_service, "embed_query", fake_embed_query)
        monkeypatch.setattr(qa_service.gemini_service, "answer_question", fake_answer)
        monkeypatch.setattr(qa_service.gemini_service, "answer_question_stream", fake_stream)

    yield setup
    app.dependency_overrides.clear()


def _authed():
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    app.dependency_overrides[get_gemini_key] = lambda: TEST_GEMINI_KEY
    app.dependency_overrides[get_db] = _fake_get_db


class TestQANonStream:
    async def test_ask_returns_answer_and_sources(self, client, mock_qa):
        mock_qa(doc_owner_id=TEST_USER_ID)
        _authed()
        resp = await client.post(f"/api/documents/{DOC_ID}/qa", json={"question": "Linear algebra là gì?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == "Đây là câu trả lời."
        assert len(body["sources"]) == 2
        assert body["sources"][0]["chunk_index"] == 0

    async def test_ask_on_doc_not_owned_404(self, client, mock_qa):
        mock_qa(doc_owner_id=uuid.uuid4())  # doc thuộc user khác
        _authed()
        resp = await client.post(f"/api/documents/{DOC_ID}/qa", json={"question": "?"})
        assert resp.status_code == 404


class TestQAStream:
    async def test_stream_sse_format(self, client, mock_qa):
        mock_qa(doc_owner_id=TEST_USER_ID)
        _authed()
        resp = await client.post(f"/api/documents/{DOC_ID}/qa/stream", json={"question": "?"})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        body = resp.text
        # Mỗi token được json.dumps (ensure_ascii) → unicode escape; frontend JSON.parse decode lại.
        # Quan trọng: newline trong token PHẢI được escape (\\n), không phá vỡ khung SSE.
        assert json.dumps("Đây ") + "\n\n" in body  # 'data:' prefix kiểm tra riêng bên dưới
        assert "data: " + json.dumps("câu\ntrả lời.") + "\n\n" in body
        assert "\\n" in body  # newline trong token bị escape
        assert body.count("\n\ndata:") + 1 == body.count("data:")  # mỗi event phân tách bằng \n\n
        assert body.rstrip().endswith("data: [DONE]")

    async def test_stream_on_doc_not_owned_404(self, client, mock_qa):
        mock_qa(doc_owner_id=uuid.uuid4())
        _authed()
        resp = await client.post(f"/api/documents/{DOC_ID}/qa/stream", json={"question": "?"})
        assert resp.status_code == 404


class TestQAGuards:
    async def test_no_auth_returns_403(self, client, mock_qa):
        mock_qa()
        # Không override auth → HTTPBearer thiếu Authorization header
        app.dependency_overrides[get_db] = _fake_get_db
        resp = await client.post(f"/api/documents/{DOC_ID}/qa", json={"question": "?"})
        assert resp.status_code == 403

    async def test_whitespace_gemini_key_returns_400(self, client, mock_qa):
        mock_qa()
        app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
        app.dependency_overrides[get_db] = _fake_get_db
        # get_gemini_key KHÔNG override → check thật chạy
        resp = await client.post(
            f"/api/documents/{DOC_ID}/qa",
            json={"question": "?"},
            headers={"X-Gemini-Key": "   "},
        )
        assert resp.status_code == 400


class TestQAStreamError:
    """Mid-stream quota error: status 200 is already committed, so the failure must
    surface as an in-band SSE error frame (no [DONE]) and the partial answer must NOT
    be persisted."""

    async def test_quota_mid_stream_emits_error_frame_and_skips_save(self, client, monkeypatch):
        created = {"called": False}
        doc_repo, chunk_repo, _ = _make_fakes(TEST_USER_ID)

        class FakeQARepo:
            def __init__(self, db=None):
                pass

            async def create(self, doc_id, question, answer, sources):
                created["called"] = True
                return _QARow(question, answer, sources)

        monkeypatch.setattr(qa_service, "DocumentRepository", doc_repo)
        monkeypatch.setattr(qa_service, "ChunkRepository", chunk_repo)
        monkeypatch.setattr(qa_service, "QARepository", FakeQARepo)

        async def fake_embed_query(question, key):
            return [0.1, 0.2, 0.3]

        async def failing_stream(question, context, key, **kw):
            yield "Đây "
            yield "là "
            raise gemini_service.GeminiQuotaError("vượt quota")

        monkeypatch.setattr(qa_service.gemini_service, "embed_query", fake_embed_query)
        monkeypatch.setattr(qa_service.gemini_service, "answer_question_stream", failing_stream)
        _authed()

        resp = await client.post(f"/api/documents/{DOC_ID}/qa/stream", json={"question": "?"})
        assert resp.status_code == 200
        body = resp.text
        assert '"error": "quota"' in body          # in-band error frame emitted
        assert "[DONE]" not in body                 # success terminator NOT sent on error
        assert created["called"] is False           # truncated answer not persisted
        app.dependency_overrides.clear()


def test_rrf_fuse_dedups_and_ranks():
    """RRF: a chunk in both lists outranks one in a single list; results deduped by id."""
    class _C:
        def __init__(self, cid):
            self.id = cid

    a, b, c = _C("a"), _C("b"), _C("c")
    # semantic ranks a>b>c ; lexical ranks c>a. a and c appear in BOTH lists.
    fused = qa_service._rrf_fuse([[a, b, c], [c, a]], rrf_k=60)
    ids = [x.id for x in fused]
    assert set(ids) == {"a", "b", "c"}   # deduped
    assert ids[0] == "a"                 # rank1 semantic + rank2 lexical → highest fused score
    assert ids[-1] == "b"                # only in one list → lowest
