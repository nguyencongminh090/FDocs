import asyncio
import json
import logging
import random
import re
from collections.abc import Callable
from functools import partial

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)


class GeminiQuotaError(Exception):
    """Gemini API quota / rate limit exhausted (maps to HTTP 429)."""


class GeminiServiceError(Exception):
    """Gemini API call failed for a non-quota reason (maps to HTTP 502)."""


_QUOTA_MSG = (
    "Đã vượt giới hạn quota Gemini API (free tier). "
    "Thử lại sau ít phút hoặc dùng tài liệu nhỏ hơn."
)

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
# text-embedding-004 was shut down by Google on 2026-01-14; gemini-embedding-001
# is the supported replacement. Its default output is 3072-dim, but pgvector's
# HNSW index caps at 2000 dims and the chunks.embedding column is vector(768),
# so embeddings are truncated to 768 via output_dimensionality.
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIM = 768
GENERATION_MODEL = "gemini-2.0-flash"

# Summary uses LARGE segments (not the 512-char retrieval chunks). Re-using the
# 512-char splitter would fan out ~one generation call per ~462 chars (>100 calls
# for a long doc) — the dominant source of 429s. Map-reduce over ~12k-char
# segments cuts that to a handful of calls while staying well inside Flash context.
SUMMARY_SEGMENT_CHARS = 12000
SUMMARY_SEGMENT_OVERLAP = 200
SUMMARY_MAP_DELAY = 1.0  # gentle inter-call spacing during the map step
# Cap segments summarized in the synchronous endpoint so the serial map step
# (each call + SUMMARY_MAP_DELAY) stays inside the < 60s summary NFR. Full-length
# summaries of very long docs belong to the async-job path (TODO.md), not here.
SUMMARY_MAX_SEGMENTS = 12

# Retry/backoff budget for transient 429s. Kept small so a quota storm surfaces
# as a clean 429 quickly instead of holding the HTTP request open past the NFR
# ceilings (Q&A < 10s, summary < 60s).
MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.8
RETRY_MAX_DELAY = 8.0
# If the server explicitly asks to wait longer than this, retrying inside the
# request is pointless — give up and surface a 429 immediately.
RETRY_AFTER_CEILING = 12.0


def _compute_batch_params(n_chunks: int) -> tuple[int, float]:
    if n_chunks <= 30:
        return n_chunks, 0.0  # single batch, no delay
    elif n_chunks <= 60:
        return 15, 5.0        # ~60 items/min
    else:
        return 10, 10.0       # ~60 items/min, conservative


KG_SCHEMA = {
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "type": {"type": "string", "enum": ["concept", "entity", "process"]},
                },
                "required": ["id", "label", "type"],
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "relation": {"type": "string"},
                },
                "required": ["source", "target", "relation"],
            },
        },
    },
    "required": ["nodes", "edges"],
}


def _make_client(api_key: str) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GENERATION_MODEL)


def _make_json_client(api_key: str, schema: dict) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        GENERATION_MODEL,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )


def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_text(text)


def _is_quota_error(exc: Exception) -> bool:
    # langchain re-wraps ResourceExhausted (e.g. in GoogleGenerativeAIError), so the
    # ResourceExhausted may sit deeper than the immediate __cause__ — walk the chain.
    cur: BaseException | None = exc
    seen = 0
    while cur is not None and seen < 5:
        if isinstance(cur, ResourceExhausted):
            return True
        cur = cur.__cause__
        seen += 1
    msg = str(exc).lower()
    return any(s in msg for s in ("429", "quota", "resource_exhausted", "resource exhausted", "rate limit"))


def _retry_after_seconds(exc: Exception) -> float | None:
    """Best-effort extraction of a server-requested wait from the error message."""
    msg = str(exc)
    for pattern in (
        r"retry_delay\s*\{\s*seconds:\s*(\d+(?:\.\d+)?)",
        r"retry in\s*(\d+(?:\.\d+)?)\s*s",
        r"retry after\s*(\d+(?:\.\d+)?)\s*second",
    ):
        m = re.search(pattern, msg, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


def _backoff_wait(attempt: int, retry_after: float | None) -> float:
    if retry_after is not None:
        base = retry_after
    else:
        base = min(RETRY_MAX_DELAY, RETRY_BASE_DELAY * (2 ** (attempt - 1)))
    jitter = random.uniform(0, base * 0.25) if base > 0 else 0.0
    # Hard cap any single sleep at the ceiling so jitter on an accepted retry_after
    # (≤ RETRY_AFTER_CEILING) cannot push one wait above it.
    return min(RETRY_AFTER_CEILING, base + jitter)


async def _call_with_backoff(factory, *, what: str, max_retries: int = MAX_RETRIES):
    """Single choke point for every Gemini call: retries transient 429s with
    exponential backoff + jitter and maps failures to GeminiQuotaError (→429) or
    GeminiServiceError (→502) so EVERY path is consistent, not just embedding."""
    attempt = 0
    while True:
        try:
            return await factory()
        except (GeminiQuotaError, GeminiServiceError):
            raise
        except Exception as e:
            if _is_quota_error(e):
                attempt += 1
                retry_after = _retry_after_seconds(e)
                if attempt > max_retries or (retry_after is not None and retry_after > RETRY_AFTER_CEILING):
                    logger.warning("Gemini quota hết khi %s (đã thử %d lần): %s", what, attempt - 1, e)
                    raise GeminiQuotaError(_QUOTA_MSG) from e
                wait = _backoff_wait(attempt, retry_after)
                logger.info("Gemini quota khi %s; thử lại %d/%d sau %.1fs", what, attempt, max_retries, wait)
                await asyncio.sleep(wait)
                continue
            logger.error("Gemini lỗi khi %s: %s", what, e)
            raise GeminiServiceError(f"Gemini API lỗi khi {what}.") from e


def _extract_text(response, what: str) -> str:
    """response.text raises ValueError when a candidate is safety-blocked or empty
    (finish_reason != STOP). Translate that into a clear 502 instead of an opaque 500."""
    try:
        return response.text
    except ValueError as e:
        reason = None
        try:
            candidates = getattr(response, "candidates", None)
            if candidates:
                reason = getattr(candidates[0], "finish_reason", None)
        except Exception:
            reason = None
        logger.warning("Gemini không trả nội dung khi %s (finish_reason=%s): %s", what, reason, e)
        raise GeminiServiceError(
            f"Gemini không trả về nội dung khi {what} (có thể bị bộ lọc an toàn chặn)."
        ) from e


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    return re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()


def _loads_or_error(raw: str, what: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Gemini trả JSON không hợp lệ khi %s: %r", what, raw[:200])
        raise GeminiServiceError(f"Gemini trả về dữ liệu không hợp lệ khi {what}.") from e


async def _embed_in_executor(fn, *, max_retries: int = MAX_RETRIES):
    # The base aembed_* helpers do not forward output_dimensionality, so the sync
    # call is run in an executor with the param bound to keep vectors at EMBEDDING_DIM.
    # Routed through _call_with_backoff so embeds get the same retry + error mapping.
    loop = asyncio.get_running_loop()
    return await _call_with_backoff(
        lambda: loop.run_in_executor(None, fn),
        what="tạo embedding",
        max_retries=max_retries,
    )


async def embed_texts(
    texts: list[str],
    api_key: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[list[float]]:
    """Embed texts in throttled batches. `progress_callback(done, total)` is invoked
    after each batch so callers (e.g. the async upload job) can report real progress
    instead of a time estimate."""
    embeddings_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
    batch_size, delay = _compute_batch_params(len(texts))
    all_embeddings: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        batch_embeddings = await _embed_in_executor(
            partial(embeddings_model.embed_documents, batch, output_dimensionality=EMBEDDING_DIM)
        )
        all_embeddings.extend(batch_embeddings)
        if progress_callback is not None:
            progress_callback(len(all_embeddings), len(texts))
        if start + batch_size < len(texts) and delay > 0:
            await asyncio.sleep(delay)
    return all_embeddings


async def embed_query(query: str, api_key: str) -> list[float]:
    embeddings_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
    # On the latency-critical Q&A path (embed_query → answer_question), budget retries
    # so embed + answer combined stay under the Q&A < 10s NFR.
    return await _embed_in_executor(
        partial(embeddings_model.embed_query, query, output_dimensionality=EMBEDDING_DIM),
        max_retries=2,
    )


def _split_for_summary(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=SUMMARY_SEGMENT_CHARS, chunk_overlap=SUMMARY_SEGMENT_OVERLAP
    )
    return splitter.split_text(text)


async def generate_summary(text: str, api_key: str) -> str:
    model = _make_client(api_key)
    segments = _split_for_summary(text)
    if not segments:
        return ""
    if len(segments) > SUMMARY_MAX_SEGMENTS:
        logger.info(
            "Tài liệu dài (%d segment); tóm tắt %d segment đầu để giữ trong NFR <60s.",
            len(segments), SUMMARY_MAX_SEGMENTS,
        )
        segments = segments[:SUMMARY_MAX_SEGMENTS]
    if len(segments) == 1:
        response = await _call_with_backoff(
            lambda: model.generate_content_async(f"Summarize the following text concisely:\n\n{segments[0]}"),
            what="tóm tắt",
        )
        return _extract_text(response, "tóm tắt")

    partial_summaries: list[str] = []
    for i, segment in enumerate(segments):
        response = await _call_with_backoff(
            lambda segment=segment: model.generate_content_async(
                f"Summarize the following text concisely:\n\n{segment}"
            ),
            what="tóm tắt",
        )
        partial_summaries.append(_extract_text(response, "tóm tắt"))
        if i < len(segments) - 1 and SUMMARY_MAP_DELAY > 0:
            await asyncio.sleep(SUMMARY_MAP_DELAY)

    combined = "\n\n".join(partial_summaries)
    final = await _call_with_backoff(
        lambda: model.generate_content_async(
            f"Synthesize these partial summaries into one coherent summary:\n\n{combined}"
        ),
        what="tổng hợp tóm tắt",
    )
    return _extract_text(final, "tổng hợp tóm tắt")


async def extract_keywords(text: str, api_key: str) -> list[str]:
    model = _make_client(api_key)
    truncated = text[:8000]
    response = await _call_with_backoff(
        lambda: model.generate_content_async(
            f"Extract the 10-15 most important keywords and concepts from this text. "
            f"Return ONLY a JSON array of strings, no explanation.\n\n{truncated}"
        ),
        what="trích xuất từ khoá",
    )
    raw = _strip_fences(_extract_text(response, "trích xuất từ khoá"))
    data = _loads_or_error(raw, "trích xuất từ khoá")
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise GeminiServiceError("Gemini trả về định dạng từ khoá không hợp lệ.")
    return data


async def score_relevance(text: str, goal: str, keywords: list[str], topic: str, api_key: str) -> dict:
    model = _make_client(api_key)
    truncated = text[:6000]
    prompt = (
        f"Evaluate how relevant this document is to the user's need.\n"
        f"User goal: {goal}\n"
        f"Keywords of interest: {', '.join(keywords)}\n"
        f"Topic: {topic}\n\n"
        f"Document excerpt:\n{truncated}\n\n"
        f"Return ONLY a JSON object: {{\"score\": <float 0-1>, \"explanation\": \"<1-2 sentences>\"}}"
    )
    response = await _call_with_backoff(
        lambda: model.generate_content_async(prompt), what="đánh giá độ liên quan"
    )
    raw = _strip_fences(_extract_text(response, "đánh giá độ liên quan"))
    data = _loads_or_error(raw, "đánh giá độ liên quan")
    try:
        score = round(float(data["score"]), 3)
        explanation = data["explanation"]
    except (KeyError, TypeError, ValueError) as e:
        raise GeminiServiceError("Gemini trả về kết quả độ liên quan không hợp lệ.") from e
    return {"relevance_score": score, "explanation": explanation}


async def generate_time_plan(sections: list | None, word_count: int, start_date: str, deadline: str, hours_per_day: float, api_key: str) -> list:
    model = _make_client(api_key)
    sections_info = json.dumps(sections) if sections else "No section structure detected; divide by word count."
    prompt = (
        f"Create a reading plan for a document.\n"
        f"Word count: {word_count}\n"
        f"Sections: {sections_info}\n"
        f"Start date: {start_date}\n"
        f"Deadline: {deadline}\n"
        f"Available hours per day: {hours_per_day}\n\n"
        f"Return ONLY a JSON array of objects: "
        f'[{{"date": "YYYY-MM-DD", "sessions": [{{"title": "section name", "estimated_minutes": 30}}]}}]'
    )
    response = await _call_with_backoff(
        lambda: model.generate_content_async(prompt), what="lập kế hoạch đọc"
    )
    raw = _strip_fences(_extract_text(response, "lập kế hoạch đọc"))
    data = _loads_or_error(raw, "lập kế hoạch đọc")
    if not isinstance(data, list):
        raise GeminiServiceError("Gemini trả về kế hoạch đọc không hợp lệ.")
    return data


async def generate_knowledge_graph(text: str, api_key: str) -> dict:
    model = _make_json_client(api_key, KG_SCHEMA)
    truncated = text[:10000]
    prompt = (
        f"Extract a knowledge graph from this text. "
        f"Identify key concepts, entities, and processes, and their relationships.\n\n{truncated}"
    )
    last_err: Exception | None = None
    for attempt in range(3):
        # _call_with_backoff re-raises GeminiQuotaError on a real 429 (→429); only
        # malformed-JSON is retried here — quota is NOT swallowed into a 500.
        response = await _call_with_backoff(
            lambda: model.generate_content_async(prompt), what="tạo knowledge graph"
        )
        raw = _extract_text(response, "tạo knowledge graph")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            last_err = e
            logger.warning("KG JSON parse lỗi (lần %d/3): %s", attempt + 1, e)
            continue
        # response_schema enforces nodes/edges, so a structural miss is not worth
        # burning more generation calls on — fail clearly instead of re-bursting.
        if not isinstance(data, dict) or "nodes" not in data or "edges" not in data:
            raise GeminiServiceError("Gemini trả về knowledge graph thiếu trường nodes/edges.")
        return data
    raise GeminiServiceError("Không thể tạo knowledge graph hợp lệ sau 3 lần thử.") from last_err


async def answer_question(question: str, context_chunks: list[str], api_key: str) -> str:
    model = _make_client(api_key)
    context = "\n\n---\n\n".join(context_chunks)
    prompt = (
        f"Answer the question based ONLY on the provided context. "
        f"If the answer is not in the context, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    response = await _call_with_backoff(
        lambda: model.generate_content_async(prompt), what="trả lời câu hỏi", max_retries=2
    )
    return _extract_text(response, "trả lời câu hỏi")


async def answer_question_stream(question: str, context_chunks: list[str], api_key: str):
    """Async generator that yields text tokens as they arrive from Gemini.

    Quota/errors mid-stream cannot change the (already-committed) HTTP status, so
    they are mapped to GeminiQuotaError/GeminiServiceError for the caller to turn
    into an SSE error frame. No retry: a stream cannot be resumed once started."""
    model = _make_client(api_key)
    context = "\n\n---\n\n".join(context_chunks)
    prompt = (
        f"Answer the question based ONLY on the provided context. "
        f"If the answer is not in the context, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    try:
        response = await model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text
    except (GeminiQuotaError, GeminiServiceError):
        raise
    except Exception as e:
        if _is_quota_error(e):
            raise GeminiQuotaError(_QUOTA_MSG) from e
        logger.error("Gemini lỗi khi stream câu trả lời: %s", e)
        raise GeminiServiceError("Gemini API lỗi khi trả lời câu hỏi.") from e
