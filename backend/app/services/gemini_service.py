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

_SYSTEM_TEXT = """\
Bạn là trợ lý học thuật của FDocs — ứng dụng giúp sinh viên đọc tài liệu học thuật.

NGÔN NGỮ: Phát hiện ngôn ngữ chủ đạo từ nội dung tài liệu được cung cấp:
- Tài liệu tiếng Việt → trả lời tiếng Việt
- Tài liệu tiếng Anh → trả lời tiếng Anh
- Tài liệu mixed → ưu tiên tiếng Việt
(Nếu user-turn chỉ định ngôn ngữ khác → ưu tiên theo user-turn)

GROUNDING: Chỉ sử dụng thông tin từ nội dung tài liệu được cung cấp trong prompt. Tổng hợp và suy luận từ nội dung được cung cấp là hợp lệ — đây vẫn là grounded. Không bổ sung từ kiến thức bên ngoài. Chỉ khi câu hỏi nhắm tới chủ đề hoàn toàn không xuất hiện trong tài liệu (kể cả dưới tên gọi hay diễn đạt khác) → dùng đúng cụm "Tài liệu không đề cập đến điều này."

ĐỊNH DẠNG: Dùng Markdown khi hữu ích:
- ### heading cho chủ đề lớn (trong summary)
- **bold** cho khái niệm quan trọng hoặc trích dẫn chứng cứ
- - bullet list cho điểm liệt kê
Không dùng Markdown cho câu trả lời ngắn (1–2 câu).
Dùng LaTeX khi có ký hiệu toán học hoặc công thức: $...$ cho inline, $$...$$ cho display block. Frontend hỗ trợ KaTeX render.

PHONG CÁCH: Học thuật, súc tích. Không mở đầu bằng: "Tất nhiên!", "Dưới đây là...", "Tôi rất vui được...", "Chắc chắn rồi!". Không kết thúc bằng: "Hy vọng hữu ích!", "Nếu bạn có câu hỏi...", "Tóm lại,".\
"""

_SYSTEM_JSON = """\
Bạn là trợ lý học thuật của FDocs — ứng dụng giúp sinh viên đọc tài liệu học thuật.

OUTPUT: Trả về ĐÚNG định dạng JSON như mô tả trong prompt. Không thêm text, markdown, code fence (```json), hay giải thích nào bên ngoài JSON. JSON minified (không có whitespace thừa).

NGÔN NGỮ: Phát hiện ngôn ngữ chủ đạo từ nội dung tài liệu. Các trường text trong JSON (label, explanation, title, relation, tên phần) phải dùng ngôn ngữ đó. Ưu tiên tiếng Việt nếu mixed.

GROUNDING: Chỉ sử dụng thông tin từ nội dung tài liệu được cung cấp. Không bổ sung từ kiến thức bên ngoài.\
"""

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
# text-embedding-004 was shut down by Google on 2026-01-14; gemini-embedding-001
# is the supported replacement. Its default output is 3072-dim, but pgvector's
# HNSW index caps at 2000 dims and the chunks.embedding column is vector(768),
# so embeddings are truncated to 768 via output_dimensionality.
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIM = 768
GENERATION_MODEL = "gemini-2.5-flash"

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


def _make_client(api_key: str, system_instruction: str = _SYSTEM_TEXT) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GENERATION_MODEL, system_instruction=system_instruction)


def _make_json_client(api_key: str, schema: dict, system_instruction: str = _SYSTEM_JSON) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        GENERATION_MODEL,
        system_instruction=system_instruction,
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


def _lang_directive(lang: str | None) -> str:
    if lang == "vi":
        return "\nHãy trả lời bằng tiếng Việt."
    if lang == "en":
        return "\nPlease respond in English."
    return ""


async def generate_summary(text: str, api_key: str, lang: str | None = None) -> str:
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

    def _map_prompt(segment: str) -> str:
        return (
            "Tóm tắt đoạn sau của tài liệu học thuật.\n\n"
            "Yêu cầu:\n"
            "- Dùng ### heading cho mỗi chủ đề hoặc luận điểm lớn\n"
            "- Dùng - bullet list cho các điểm chính dưới mỗi heading\n"
            "- Giữ nguyên thuật ngữ kỹ thuật và tên riêng từ tài liệu\n\n"
            f"Nội dung:\n{segment}"
            + _lang_directive(lang)
        )

    if len(segments) == 1:
        response = await _call_with_backoff(
            lambda: model.generate_content_async(_map_prompt(segments[0])),
            what="tóm tắt",
        )
        return _extract_text(response, "tóm tắt")

    partial_summaries: list[str] = []
    for i, segment in enumerate(segments):
        response = await _call_with_backoff(
            lambda segment=segment: model.generate_content_async(_map_prompt(segment)),
            what="tóm tắt",
        )
        partial_summaries.append(_extract_text(response, "tóm tắt"))
        if i < len(segments) - 1 and SUMMARY_MAP_DELAY > 0:
            await asyncio.sleep(SUMMARY_MAP_DELAY)

    combined = "\n\n".join(partial_summaries)
    reduce_prompt = (
        "Tổng hợp các tóm tắt riêng lẻ sau thành một bản tóm tắt duy nhất, mạch lạc.\n\n"
        "Yêu cầu:\n"
        "- Dùng ## heading cho các chủ đề lớn của toàn tài liệu\n"
        "- Dùng - bullet list cho điểm chính dưới mỗi heading\n"
        "- Loại bỏ nội dung trùng lặp giữa các phần\n"
        "- Sắp xếp theo luồng logic của tài liệu, không phải theo thứ tự các tóm tắt đầu vào\n\n"
        f"Các tóm tắt riêng lẻ:\n{combined}"
        + _lang_directive(lang)
    )
    final = await _call_with_backoff(
        lambda: model.generate_content_async(reduce_prompt),
        what="tổng hợp tóm tắt",
    )
    return _extract_text(final, "tổng hợp tóm tắt")


async def extract_keywords(text: str, api_key: str) -> list[str]:
    model = _make_client(api_key, system_instruction=_SYSTEM_JSON)
    truncated = text[:8000]
    response = await _call_with_backoff(
        lambda: model.generate_content_async(
            "Trích xuất 10–15 từ khóa và khái niệm quan trọng nhất từ đoạn văn này.\n\n"
            "Tiêu chí ưu tiên (theo thứ tự):\n"
            "1. Thuật ngữ kỹ thuật đặc thù của lĩnh vực học thuật\n"
            "2. Tên phương pháp, mô hình, hoặc framework được đề cập\n"
            "3. Khái niệm xuất hiện nhiều lần hoặc được định nghĩa rõ ràng\n\n"
            'Trả về JSON array: ["từ khóa 1", "khái niệm 2", ...]\n\n'
            f"Nội dung:\n{truncated}"
        ),
        what="trích xuất từ khoá",
    )
    raw = _strip_fences(_extract_text(response, "trích xuất từ khoá"))
    data = _loads_or_error(raw, "trích xuất từ khoá")
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise GeminiServiceError("Gemini trả về định dạng từ khoá không hợp lệ.")
    return data


async def score_relevance(text: str, goal: str, keywords: list[str], topic: str, api_key: str, lang: str | None = None) -> dict:
    model = _make_client(api_key, system_instruction=_SYSTEM_JSON)
    truncated = text[:6000]
    keywords_joined = ", ".join(keywords)
    prompt = (
        "Đánh giá mức độ phù hợp của tài liệu với nhu cầu của người dùng.\n\n"
        "Nhu cầu người dùng:\n"
        f"- Mục tiêu học tập: {goal}\n"
        f"- Từ khóa quan tâm: {keywords_joined}\n"
        f"- Chủ đề: {topic}\n\n"
        f"Trích đoạn tài liệu:\n{truncated}\n\n"
        "Thang điểm:\n"
        "- 0.85–1.0: Trực tiếp phục vụ mục tiêu, bao phủ phần lớn từ khóa\n"
        "- 0.60–0.84: Liên quan đáng kể, có nội dung hữu ích rõ ràng\n"
        "- 0.35–0.59: Liên quan gián tiếp, chỉ chạm một phần nhu cầu\n"
        "- 0.10–0.34: Ít liên quan, thông tin ngoài lề\n"
        "- 0.00–0.09: Không phù hợp\n\n"
        'Trả về JSON: {"score": <float 0.0–1.0, 2 chữ số thập phân>, '
        '"explanation": "<2–3 câu: (1) điểm số được cho vì lý do gì, '
        "(2) điểm mạnh của tài liệu với nhu cầu này, "
        '(3) điểm còn thiếu nếu có. Dùng **bold** cho lý do chính.>"}'
        + _lang_directive(lang)
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
    model = _make_client(api_key, system_instruction=_SYSTEM_JSON)
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
        "Trích xuất knowledge graph từ đoạn văn học thuật sau.\n\n"
        "Quy tắc trích xuất Nodes (tối đa 20):\n"
        "- Chọn những concept, entity, hoặc process QUAN TRỌNG NHẤT — ưu tiên chất lượng hơn số lượng\n"
        '- type "concept": khái niệm lý thuyết, định nghĩa, nguyên lý\n'
        '- type "entity": tên riêng, phương pháp, công cụ, tổ chức\n'
        '- type "process": quy trình, thuật toán, chuỗi bước\n'
        '- Loại bỏ node quá chung chung như "nghiên cứu", "tài liệu", "kết quả"\n\n'
        "Quy tắc trích xuất Edges:\n"
        '- Mỗi edge là động từ hoặc cụm động từ ngắn (tối đa 4 từ): "sử dụng", "dẫn đến", "bao gồm", "được định nghĩa bằng", "ảnh hưởng đến"\n'
        '- Không dùng noun phrase làm edge label ("dependency of", "part of")\n\n'
        f"Nội dung:\n{truncated}"
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


def _qa_prompt(question: str, context: str, lang: str | None = None) -> str:
    return (
        "Trả lời câu hỏi dựa trên ngữ cảnh được cung cấp dưới đây.\n"
        "Trả lời bằng cùng ngôn ngữ với câu hỏi.\n\n"
        "Quy tắc bắt buộc:\n"
        "- Chỉ dùng thông tin có trong ngữ cảnh. KHÔNG bổ sung kiến thức bên ngoài. Được phép TỔNG HỢP và SUY LUẬN từ chính ngữ cảnh — đây vẫn là grounded.\n"
        "- Nếu câu trả lời rút ra được từ ngữ cảnh (trực tiếp hoặc bằng tổng hợp): trả lời trực tiếp, súc tích. Dùng **bold** cho phần chứng cứ quan trọng.\n"
        "- Nếu ngữ cảnh LIÊN QUAN câu hỏi nhưng chỉ phủ một phần: trả lời đầy đủ phần có căn cứ trong tài liệu, rồi nêu ngắn gọn phần nào tài liệu chưa đề cập. KHÔNG từ chối toàn bộ chỉ vì thiếu một phần.\n"
        "- Một câu hỏi được coi là LIÊN QUAN nếu ngữ cảnh có nhắc tới khái niệm, thuật ngữ hoặc chủ đề mà câu hỏi nhắm tới — kể cả khi dùng từ ngữ, tên gọi hoặc viết tắt khác với câu hỏi.\n"
        "- Câu hỏi tổng quan ('nói về gì?', 'chủ đề là gì?', 'tóm tắt nội dung?'): tổng hợp từ các đoạn ngữ cảnh.\n"
        '- CHỈ khi ngữ cảnh hoàn toàn không chứa khái niệm, thuật ngữ hay chủ đề nào liên quan: viết đúng cụm "Tài liệu không đề cập đến điều này." Không dùng câu này khi ngữ cảnh có nội dung liên quan dù chỉ một phần.\n'
        "- Độ dài: tối đa 3–4 đoạn ngắn; câu trả lời đơn giản thì 1–2 câu là đủ.\n\n"
        f"Ngữ cảnh:\n{context}\n\n"
        f"Câu hỏi: {question}"
        + _lang_directive(lang)
    )


async def answer_question(question: str, context_chunks: list[str], api_key: str, lang: str | None = None) -> str:
    model = _make_client(api_key)
    context = "\n\n---\n\n".join(context_chunks)
    prompt = _qa_prompt(question, context, lang)
    response = await _call_with_backoff(
        lambda: model.generate_content_async(prompt), what="trả lời câu hỏi", max_retries=2
    )
    return _extract_text(response, "trả lời câu hỏi")


async def answer_question_stream(question: str, context_chunks: list[str], api_key: str, lang: str | None = None):
    """Async generator that yields text tokens as they arrive from Gemini.

    Quota/errors mid-stream cannot change the (already-committed) HTTP status, so
    they are mapped to GeminiQuotaError/GeminiServiceError for the caller to turn
    into an SSE error frame. No retry: a stream cannot be resumed once started."""
    model = _make_client(api_key)
    context = "\n\n---\n\n".join(context_chunks)
    prompt = _qa_prompt(question, context, lang)
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
