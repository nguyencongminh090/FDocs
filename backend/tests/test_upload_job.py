"""Test cho upload_job_service — pipeline nền, progress events, SSE stream, phân quyền."""
import asyncio
import json
import uuid

import pytest
from fastapi import HTTPException

from app.services import upload_job_service as ujs
from app.services.gemini_service import GeminiQuotaError, GeminiServiceError
from tests.conftest import TEST_GEMINI_KEY, TEST_USER_ID

OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
DOC_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")


class _FakeSession:
    async def __aenter__(self):
        return None

    async def __aexit__(self, *exc):
        return False


class _FakeDoc:
    id = DOC_ID


def _drain(queue: asyncio.Queue) -> list[dict]:
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())
    return events


@pytest.fixture(autouse=True)
def _clean_registry():
    ujs._jobs.clear()
    yield
    ujs._jobs.clear()


@pytest.fixture
def no_expire(monkeypatch):
    """Neutralise the 300s _expire task so it doesn't linger past the test loop."""
    async def _noop(job_id):
        return

    monkeypatch.setattr(ujs, "_expire", _noop)


def _wire_pipeline(monkeypatch, create_document):
    monkeypatch.setattr(ujs, "AsyncSessionLocal", lambda: _FakeSession())

    class FakeService:
        def __init__(self, db):
            pass

    FakeService.create_document = create_document
    monkeypatch.setattr(ujs, "DocumentService", FakeService)


class TestEnqueue:
    async def test_enqueue_registers_job_and_returns_id(self, monkeypatch, no_expire):
        async def fake_run(job_id, data, key):
            return

        monkeypatch.setattr(ujs, "_run", fake_run)
        job_id = ujs.enqueue(TEST_USER_ID, {"extracted_text": "x"}, TEST_GEMINI_KEY)
        await asyncio.sleep(0)  # let the scheduled task drain
        job = ujs.get_job(job_id)
        assert job is not None
        assert job.user_id == TEST_USER_ID
        assert job.status == "processing"


class TestRunPipeline:
    async def test_happy_path_emits_progress_then_done_with_doc_id(self, monkeypatch, no_expire):
        async def create_document(self, user_id, data, gemini_key, progress_cb=None):
            progress_cb("chunking", 5)
            progress_cb("embedding", 50)
            progress_cb("saving", 95)
            return _FakeDoc()

        _wire_pipeline(monkeypatch, create_document)
        job_id = ujs.create_job(TEST_USER_ID)
        job = ujs.get_job(job_id)

        await ujs._run(job_id, {"extracted_text": "x"}, TEST_GEMINI_KEY)
        await asyncio.sleep(0)

        events = _drain(job.queue)
        steps = [(e["step"], e["progress"]) for e in events]
        assert ("chunking", 5) in steps
        assert ("embedding", 50) in steps
        assert ("saving", 95) in steps

        terminal = events[-1]
        assert terminal["status"] == "done"
        assert terminal["progress"] == 100
        assert terminal["doc_id"] == str(DOC_ID)
        assert job.terminal_event == terminal

    async def test_quota_error_emits_error_event_no_doc(self, monkeypatch, no_expire):
        async def create_document(self, user_id, data, gemini_key, progress_cb=None):
            raise GeminiQuotaError("Đã vượt giới hạn quota Gemini API.")

        _wire_pipeline(monkeypatch, create_document)
        job_id = ujs.create_job(TEST_USER_ID)
        job = ujs.get_job(job_id)

        await ujs._run(job_id, {"extracted_text": "x"}, TEST_GEMINI_KEY)
        await asyncio.sleep(0)

        terminal = _drain(job.queue)[-1]
        assert terminal["status"] == "error"
        assert terminal["error"] == "quota"
        assert "quota" in terminal["detail"].lower()
        assert "doc_id" not in terminal
        assert job.status == "error"

    async def test_service_error_maps_to_service_kind(self, monkeypatch, no_expire):
        async def create_document(self, user_id, data, gemini_key, progress_cb=None):
            raise GeminiServiceError("Gemini API lỗi.")

        _wire_pipeline(monkeypatch, create_document)
        job_id = ujs.create_job(TEST_USER_ID)
        job = ujs.get_job(job_id)

        await ujs._run(job_id, {"extracted_text": "x"}, TEST_GEMINI_KEY)
        await asyncio.sleep(0)

        assert _drain(job.queue)[-1]["error"] == "service"

    async def test_unexpected_error_maps_to_server_kind(self, monkeypatch, no_expire):
        async def create_document(self, user_id, data, gemini_key, progress_cb=None):
            raise RuntimeError("boom")

        _wire_pipeline(monkeypatch, create_document)
        job_id = ujs.create_job(TEST_USER_ID)
        job = ujs.get_job(job_id)

        await ujs._run(job_id, {"extracted_text": "x"}, TEST_GEMINI_KEY)
        await asyncio.sleep(0)

        terminal = _drain(job.queue)[-1]
        assert terminal["error"] == "server"
        # Internal error text must not leak to the client detail.
        assert "boom" not in terminal["detail"]


class TestProgressResponseAuth:
    def test_unknown_job_404(self):
        with pytest.raises(HTTPException) as exc:
            ujs.build_progress_response("nope", TEST_USER_ID)
        assert exc.value.status_code == 404

    def test_other_user_job_404(self):
        job_id = ujs.create_job(TEST_USER_ID)
        with pytest.raises(HTTPException) as exc:
            ujs.build_progress_response(job_id, OTHER_USER_ID)
        assert exc.value.status_code == 404


class TestProgressStream:
    async def test_streams_queued_events_until_terminal(self):
        job_id = ujs.create_job(TEST_USER_ID)
        job = ujs.get_job(job_id)
        job.queue.put_nowait({"status": "processing", "step": "embedding", "progress": 50})
        job.queue.put_nowait({"status": "done", "step": "done", "progress": 100, "doc_id": str(DOC_ID)})

        resp = ujs.build_progress_response(job_id, TEST_USER_ID)
        body = "".join([chunk async for chunk in resp.body_iterator])

        assert '"progress": 50' in body
        frames = [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: ")]
        assert frames[-1]["status"] == "done"
        assert frames[-1]["doc_id"] == str(DOC_ID)

    async def test_late_connect_replays_terminal_state_once(self):
        job_id = ujs.create_job(TEST_USER_ID)
        job = ujs.get_job(job_id)
        # Job already finished and its queue was drained by an earlier connection.
        job.terminal_event = {"status": "done", "step": "done", "progress": 100, "doc_id": str(DOC_ID)}

        resp = ujs.build_progress_response(job_id, TEST_USER_ID)
        frames = [
            json.loads(line[6:])
            async for chunk in resp.body_iterator
            for line in chunk.splitlines()
            if line.startswith("data: ")
        ]
        assert frames == [job.terminal_event]
