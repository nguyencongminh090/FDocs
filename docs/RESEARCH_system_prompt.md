# Research: System Prompt Design cho FDocs

> **Ngày**: 2026-06-17 | **Worker**: Research Worker

---

## Root Cause Analysis

### Trạng thái hiện tại

Đọc `backend/app/services/gemini_service.py`, xác định:

```python
def _make_client(api_key: str) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GENERATION_MODEL)   # ← không có system_instruction

def _make_json_client(api_key: str, schema: dict) -> genai.GenerativeModel:
    return genai.GenerativeModel(
        GENERATION_MODEL,
        generation_config=genai.GenerationConfig(    # ← chỉ có generation_config
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
```

**Không có `system_instruction` nào** được truyền vào — tất cả context về role, ngôn ngữ, format đang nằm trong user-turn prompt.

### Hệ quả quan sát được

Phân tích từng prompt hiện tại:

| Feature | Prompt gốc | Vấn đề |
|---|---|---|
| Summary | `"Summarize the following text concisely"` | English → model trả lời tiếng Anh; không có format hướng dẫn |
| Summary (reduce) | `"Synthesize these partial summaries into one coherent summary"` | Như trên |
| Keywords | `"Extract 10-15 most important keywords..."` | Kết quả có thể là tiếng Anh cho tài liệu tiếng Việt |
| Relevance | `"Return ONLY a JSON object: {score, explanation}"` | explanation chỉ "1-2 sentences" — quá ít sau khi có markdown render |
| Time Plan | JSON prompt đầy đủ cấu trúc | Ổn — output là structured JSON, ngôn ngữ không quan trọng |
| Knowledge Graph | `"Extract a knowledge graph..."` | Schema enforced — ngôn ngữ node labels có thể là English |
| Q&A | `"Answer the question based ONLY on the provided context"` | Không có format hướng dẫn; không có language constraint |

### Screenshot evidence

Trong screenshot được chia sẻ bởi user: Summary panel hiển thị response tiếng Anh (`"This document... It systematically outlines..."`) mặc dù UI app là tiếng Việt và người dùng là sinh viên Việt Nam.

---

## Giải Pháp Đề Xuất

### Option A — Một Global System Instruction cho tất cả features

Truyền cùng một `system_instruction` vào `_make_client` và `_make_json_client`.

**Implementation:**

```python
_SYSTEM_INSTRUCTION = """\
Bạn là trợ lý học thuật của FDocs — ứng dụng hỗ trợ sinh viên đọc tài liệu học thuật.

## Vai trò
Phân tích tài liệu học thuật và trả lời câu hỏi dựa trên nội dung được cung cấp.

## Nguyên tắc bắt buộc
- NGÔN NGỮ: Nếu tài liệu viết bằng tiếng Việt → trả lời bằng tiếng Việt. \
Nếu tài liệu viết bằng tiếng Anh → trả lời bằng tiếng Anh. \
Nếu tài liệu là mixed → ưu tiên tiếng Việt.
- ĐỘ CHÍNH XÁC: Chỉ sử dụng thông tin từ tài liệu được cung cấp. \
Không bịa thêm nội dung ngoài tài liệu.
- PHONG CÁCH: Học thuật, súc tích, không thêm lời mở đầu/kết thúc sáo rỗng \
("Dưới đây là...", "Tóm lại,..." ở đầu câu).
- ĐỊNH DẠNG: Dùng Markdown để cấu trúc output — \
headings (##, ###), bold (**term**), bullet list (- item) khi phù hợp.
"""

def _make_client(api_key: str) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GENERATION_MODEL, system_instruction=_SYSTEM_INSTRUCTION)

def _make_json_client(api_key: str, schema: dict) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        GENERATION_MODEL,
        system_instruction=_SYSTEM_INSTRUCTION,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
```

**Pros:**
- Một chỗ duy nhất để maintain — thay đổi một lần, áp dụng toàn bộ
- Không cần sửa từng user-turn prompt
- Gemini xử lý system_instruction ở tầng riêng biệt với user prompt (token cache-friendly)

**Cons:**
- "Dùng Markdown" áp dụng cho cả JSON-output features (keywords, time plan) — model phải đủ thông minh để hiểu "khi phù hợp" nghĩa là bỏ qua khi đã có `response_mime_type=application/json`
- Không thể tùy chỉnh riêng per-feature

**Độ phức tạp implement:** Thấp — 3 dòng thay đổi  
**Risk:** Thấp — `system_instruction` không override JSON schema, Gemini vẫn theo schema

---

### Option B — Per-Feature System Instructions

Tạo 2 hoặc 3 system instruction profile:
1. `_SYSTEM_TEXT` — dùng cho Summary, Q&A (output markdown text)
2. `_SYSTEM_JSON` — dùng cho Keywords, Relevance, Time Plan, KG (output JSON)

```python
_SYSTEM_TEXT = """\
Bạn là trợ lý học thuật của FDocs.
- Ngôn ngữ: match ngôn ngữ tài liệu (ưu tiên tiếng Việt nếu mixed)
- Chỉ dùng thông tin từ tài liệu được cung cấp
- Dùng Markdown để cấu trúc output (## heading, **bold**, - bullet)
- Không thêm lời mở đầu sáo rỗng
"""

_SYSTEM_JSON = """\
Bạn là trợ lý học thuật của FDocs.
- Ngôn ngữ: match ngôn ngữ tài liệu (ưu tiên tiếng Việt nếu mixed)
- Trả về ĐÚNG định dạng JSON được yêu cầu, không thêm text ngoài JSON
- Chỉ dùng thông tin từ tài liệu được cung cấp
"""

# Summary, Q&A dùng _make_client với _SYSTEM_TEXT
# Keywords, Relevance, TimePlan, KG dùng _make_json_client với _SYSTEM_JSON
```

**Pros:**
- Tách biệt rõ ràng giữa text và JSON output
- JSON features không bị "nhiễu" bởi markdown instruction

**Cons:**
- 2 factory functions × 2 system instructions → thêm complexity
- Khó maintain hơn khi cần thay đổi persona

**Độ phức tạp implement:** Trung bình  
**Risk:** Thấp

---

### Option C — Cải thiện User-Turn Prompts + Global Instruction (Hybrid)

Giữ Option A (global system instruction), nhưng cũng cải thiện các user-turn prompts quan trọng:

**Summary prompts cải thiện:**
```python
# Thay vì:
f"Summarize the following text concisely:\n\n{segment}"

# Dùng:
f"Tóm tắt phần nội dung sau của tài liệu học thuật. "
f"Sử dụng heading (##) cho các chủ đề lớn và bullet list cho điểm chính.\n\n{segment}"
```

**Q&A prompt cải thiện:**
```python
# Thay vì:
f"Answer the question based ONLY on the provided context. If the answer is not in the context, say so."

# Dùng:
f"Trả lời câu hỏi dựa CHỈ VÀO ngữ cảnh được cung cấp. "
f"Nếu câu trả lời không có trong ngữ cảnh, nói rõ điều đó. "
f"Trích dẫn phần liên quan nếu hữu ích.\n\n"
```

**Relevance explanation cải thiện:**
```python
# Thay vì "1-2 sentences":
f"Return ONLY a JSON object: {{\"score\": <float 0-1>, "
f"\"explanation\": \"<2-3 câu phân tích lý do điểm số, dùng Markdown bold cho các điểm chính>\"}}"
```

**Pros:**
- Kiểm soát tốt nhất — system instruction + per-feature prompt đều clear
- Dễ A/B test từng feature riêng lẻ

**Cons:**
- Nhiều chỗ cần sửa nhất (6 prompts)
- Một số sửa đổi có thể ảnh hưởng JSON parsing (đặc biệt relevance)

**Độ phức tạp implement:** Trung bình-Cao  
**Risk:** Trung bình (cần test lại JSON parsing sau khi sửa prompts)

---

## Khuyến Nghị

**Implement Option A trước, sau đó apply Option C cải thiện có chọn lọc.**

**Lý do:**
1. Option A giải quyết 80% vấn đề (ngôn ngữ + format) với 3 dòng code — zero risk
2. Option C cải thiện thêm summary và Q&A quality mà không đụng đến JSON features
3. Option B (per-feature) là over-engineering ở thời điểm này — không đủ evidence để justify complexity

**Thứ tự ưu tiên:**
1. ✅ **Global system instruction** (Option A) — bắt buộc, làm trước
2. ✅ **Summary prompts** (Option C) — làm ngay sau, vì summary là feature nhìn thấy rõ nhất
3. ⏳ **Q&A prompt** (Option C) — làm sau nếu user feedback thấy Q&A trả lời tiếng Anh
4. ⏳ **Relevance explanation** — làm sau khi có markdown render (Phase 10 đã xong)

---

## Note về Kỹ Thuật

### Cách Gemini xử lý system_instruction

```python
genai.GenerativeModel(
    model_name,
    system_instruction="..."   # ← ContentType, không phải string thường
)
```

Gemini Python SDK accept `system_instruction` là `str | Content | list[Part]`. Khi truyền `str`, SDK tự wrap thành `Content(role="system", parts=[Part(text=...)])`. System instruction **không tốn token trong user-turn** và được cache riêng → token-efficient.

### Tương thích với `_make_json_client`

`system_instruction` và `generation_config` (JSON schema) là 2 params độc lập — không conflict. Model vẫn tuân theo JSON schema khi `response_mime_type="application/json"`.

### Language Detection

Không cần implement language detection logic trong code. Cách đơn giản nhất: hướng dẫn model trong system instruction tự detect từ nội dung tài liệu được cung cấp (model đủ capable để làm điều này).

---

## Action Items

Cho **Backend Worker** (`/as-backend`):

1. **[P0]** Thêm `_SYSTEM_INSTRUCTION` constant vào `gemini_service.py` (trước `_make_client`)
2. **[P0]** Sửa `_make_client`: thêm `system_instruction=_SYSTEM_INSTRUCTION`
3. **[P0]** Sửa `_make_json_client`: thêm `system_instruction=_SYSTEM_INSTRUCTION`
4. **[P1]** Cải thiện summary prompt: thêm instruction về markdown structure và ngôn ngữ
5. **[P1]** Cải thiện summary reduce prompt: thêm instruction tương tự
6. **[P2]** Cải thiện Q&A prompt: chuyển sang tiếng Việt, thêm "trích dẫn nếu hữu ích"

**Test cần có sau khi implement:**
- Chạy `pytest` đảm bảo 113 tests vẫn pass (prompts thay đổi không ảnh hưởng unit tests vì đã mock)
- Manual test: upload tài liệu tiếng Việt → generate summary → verify response là tiếng Việt với markdown
- Manual test: upload tài liệu tiếng Anh → verify response là tiếng Anh
