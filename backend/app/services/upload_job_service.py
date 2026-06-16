"""Async upload pipeline + progress reporting.

POST /api/documents enqueues a job and returns 202 + job_id immediately, so the
slow chunk→embed→save pipeline (100-170s for large docs) no longer holds the HTTP
request open and risks a 504. The client then watches GET /api/upload/{job_id}/progress.

Job state lives ONLY in process memory. The BYOK Gemini key is held in RAM for the
job's lifetime and never persisted (BYOK rule). Trade-off: single-process only — with
multiple uvicorn workers the POST and the progress stream may land on different workers,
so the stream would 404. Documented in docs/API.md; a shared bus (e.g. Redis) is the
multi-worker fix and is out of P1 scope.
"""
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from app.database import AsyncSessionLocal
from app.services import gemini_service
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

# Keep a finished job's state around briefly so a client that reconnects (or connects
# late, after a very fast job) can still read the terminal event before it's evicted.
JOB_TTL_SECONDS = 300
# Emit an SSE comment if no progress event arrives within this window, so idle proxies
# don't drop the connection during a slow embedding batch.
KEEPALIVE_SECONDS = 15

_TERMINAL_STATUSES = ("done", "error")

_jobs: dict[str, "UploadJob"] = {}


@dataclass
class UploadJob:
    job_id: str
    user_id: uuid.UUID
    status: str = "processing"  # processing | done | error
    step: str = "queued"  # queued | chunking | embedding | saving | done
    progress: int = 0  # 0..100
    doc_id: str | None = None
    error: str | None = None  # error kind: quota | service | server
    detail: str | None = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    terminal_event: dict | None = None

    def snapshot(self) -> dict:
        event = {"status": self.status, "step": self.step, "progress": self.progress}
        if self.doc_id:
            event["doc_id"] = self.doc_id
        if self.error:
            event["error"] = self.error
        if self.detail:
            event["detail"] = self.detail
        return event


def create_job(user_id: uuid.UUID) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = UploadJob(job_id=job_id, user_id=user_id)
    return job_id


def get_job(job_id: str) -> UploadJob | None:
    return _jobs.get(job_id)


def enqueue(user_id: uuid.UUID, data: dict, gemini_key: str) -> str:
    """Register a job and start its pipeline in the background. Returns the job_id."""
    job_id = create_job(user_id)
    asyncio.create_task(_run(job_id, data, gemini_key))
    return job_id


def _push(job: UploadJob) -> None:
    job.queue.put_nowait(job.snapshot())


async def _run(job_id: str, data: dict, gemini_key: str) -> None:
    job = _jobs.get(job_id)
    if job is None:  # evicted before it started (only possible under manual pruning)
        return
    try:
        # The request-scoped session is already closed by the time this background task
        # runs, so the pipeline opens (and owns) its own session.
        async with AsyncSessionLocal() as db:
            def progress_cb(step: str, percent: int) -> None:
                job.step = step
                job.progress = percent
                _push(job)

            doc = await DocumentService(db).create_document(
                job.user_id, data, gemini_key, progress_cb=progress_cb
            )
        job.status = "done"
        job.step = "done"
        job.progress = 100
        job.doc_id = str(doc.id)
    except gemini_service.GeminiQuotaError as e:
        _set_error(job, "quota", str(e))
    except gemini_service.GeminiServiceError as e:
        _set_error(job, "service", str(e))
    except Exception as e:
        logger.error("Upload job %s thất bại: %s", job_id, e, exc_info=True)
        _set_error(job, "server", "Lỗi máy chủ khi xử lý tài liệu.")
    finally:
        job.terminal_event = job.snapshot()
        _push(job)
        asyncio.create_task(_expire(job_id))


def _set_error(job: UploadJob, kind: str, detail: str) -> None:
    job.status = "error"
    job.error = kind
    job.detail = detail


async def _expire(job_id: str) -> None:
    await asyncio.sleep(JOB_TTL_SECONDS)
    _jobs.pop(job_id, None)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def build_progress_response(job_id: str, user_id: uuid.UUID) -> StreamingResponse:
    job = _jobs.get(job_id)
    # 404 (not 403) when the job belongs to someone else, so an attacker can't probe
    # which job_ids exist by status code.
    if job is None or job.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload job not found")

    async def event_generator():
        # Reconnect / late connect after the job already finished and its events were
        # drained: replay the terminal state once so the client isn't left hanging.
        if job.terminal_event is not None and job.queue.empty():
            yield _sse(job.terminal_event)
            return
        while True:
            try:
                event = await asyncio.wait_for(job.queue.get(), timeout=KEEPALIVE_SECONDS)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue
            yield _sse(event)
            if event.get("status") in _TERMINAL_STATUSES:
                return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
