# Research: System Prompt Design — Per-Feature (Option B Approved)

> **Ngày**: 2026-06-17 | **Worker**: Research Worker  
> **Decision**: Option B (Per-Feature) — đã được approve  
> **Thay thế**: `RESEARCH_system_prompt.md` — báo cáo này có đầy đủ hơn và phản ánh decision mới

---

## Tóm tắt Decision

Sử dụng **2 system instruction profiles** — không phải 1 global, không phải 6 per-function:
- `_SYSTEM_TEXT` — cho Summary, Q&A (text output, markdown)
- `_SYSTEM_JSON` — cho Keywords, Relevance, Time Plan, Knowledge Graph (JSON output)

Implement bằng cách thêm optional param vào 2 factory functions hiện có, không tạo thêm function mới.

---

## Bằng Chứng Từ Research

### 1. Tại sao system instruction quan trọng trong production

Từ Google AI documentation và Brainfile 2026:
- System instruction được xử lý ở tầng riêng biệt với user prompt — **token caching tự động** (implicit cache mặc định cho Gemini 2.5+, chi phí 10% so với token thường).
- Ordering matter: Google khuyến nghị **Persona → Rules → Format** — model follow đúng thứ tự đó.
- Gemini 2.5-flash responds best to prompts that are "direct, well-structured, and clearly define the task and any constraints" — **không dài dòng, không mơ hồ**.

### 2. Tại sao cần tách Text và JSON

Từ Gemini structured output docs:
- `_make_json_client` dùng `response_mime_type="application/json"` — model được constrain ở tầng config. System instruction "dùng Markdown" tạo **tension ngầm** với JSON-mode config.
- `extract_keywords`, `score_relevance`, `generate_time_plan` dùng `_make_client` nhưng expect JSON thuần — đây là nhóm có rủi ro cao nhất nếu system instruction nói "use Markdown".
- Giải pháp: `_SYSTEM_JSON` explicitly ban markdown, `_SYSTEM_TEXT` encourage markdown — **zero tension**.

### 3. Tại sao grounding instruction quan trọng với RAG

Từ nghiên cứu 2025 (Nature + Frontiers AI):
- Prompt-based grounding (explicit "only use provided context") giảm hallucination ~22 percentage points.
- RAG systems có hallucination rate < 2% khi grounded đúng cách, vs 58–88% khi không grounded (legal domain).
- FDocs đã có RAG pipeline — system instruction grounding **amplify** hiệu quả của retrieval, không chỉ "nice to have".
- Pattern hiệu quả nhất: **rõ ràng + negative** — vừa nói "dùng thông tin trong tài liệu" vừa nói "không bịa thêm".

### 4. Language detection — nên để model tự detect

Không cần code language detection. Gemini đủ capable để detect từ content. Điều kiện cần: **explicit instruction** với ví dụ cụ thể, không chỉ "match document language" chung chung.

---

## Phân Tích Từng Feature

### Feature 1: `generate_summary`

**Vấn đề hiện tại:**
```python
f"Summarize the following text concisely:\n\n{segment}"
```
- "concisely" không định nghĩa format → model tự chọn, thường là paragraph đơn
- Tiếng Anh → model trả tiếng Anh
- Không có structure guidance → sau khi Phase 10 thêm markdown render, output vẫn là plain text

**Cần từ system instruction**: language matching, markdown structure  
**Cần từ user-turn improvement**: chỉ định rõ headings + bullets

---

### Feature 2: `answer_question` / `answer_question_stream`

**Vấn đề hiện tại:**
```python
f"Answer the question based ONLY on the provided context. "
f"If the answer is not in the context, say so.\n\n"
```
- Đã có grounding ("ONLY on provided context") — tốt
- Nhưng không có language instruction → model reply theo ngôn ngữ câu hỏi của user
- Không có citation guidance → không trích dẫn phần cụ thể trong tài liệu

**Risk cao nhất**: hallucination khi context không có câu trả lời — model có thể tự bịa thay vì nói "không có trong tài liệu"

---

### Feature 3: `extract_keywords`

**Vấn đề hiện tại:**
```python
f"Return ONLY a JSON array of strings, no explanation.\n\n{truncated}"
```
- Tiếng Anh → keywords có thể là tiếng Anh cho tài liệu tiếng Việt
- `_make_client` với global "use Markdown" (Option A) → tension với "ONLY a JSON array"

**Với `_SYSTEM_JSON`**: language matching cho string values, no markdown tension.

---

### Feature 4: `score_relevance`

**Vấn đề hiện tại:**
```python
f"Return ONLY a JSON object: {{\"score\": <float 0-1>, \"explanation\": \"<1-2 sentences>\"}}"
```
- `explanation` field: tiếng Anh, quá ngắn (1-2 sentences), không có bold cho key points
- Phase 10 đã thêm markdown render cho explanation — nhưng model chưa biết dùng markdown trong explanation

**Với `_SYSTEM_JSON`**: language matching, cho phép light markdown trong explanation field (bold only, không có heading).

---

### Feature 5: `generate_time_plan`

**Output là date/title structured JSON** — không cần nhiều thay đổi.  
Section titles trong JSON sẽ tự match ngôn ngữ tài liệu nhờ `_SYSTEM_JSON`.

---

### Feature 6: `generate_knowledge_graph`

**Vấn đề hiện tại:**
```python
f"Extract a knowledge graph from this text. "
f"Identify key concepts, entities, and processes, and their relationships.\n\n{truncated}"
```
- Node labels và edge relations: thường là tiếng Anh dù tài liệu tiếng Việt
- `_make_json_client` với schema → output đã enforced structure
- Language matching bị thiếu

**Với `_SYSTEM_JSON`**: language matching cho `label` và `relation` fields.

---

## System Instructions Được Đề Xuất

> **Note**: Đây là nội dung đề xuất để Backend Worker implement. Không phải production code.

### `_SYSTEM_TEXT` — Dùng cho Summary, Q&A

```
Bạn là trợ lý học thuật của FDocs — ứng dụng giúp sinh viên đọc tài liệu học thuật.

## Nguyên tắc

NGÔN NGỮ: Phát hiện ngôn ngữ chủ đạo từ nội dung tài liệu được cung cấp:
- Tài liệu tiếng Việt → trả lời tiếng Việt
- Tài liệu tiếng Anh → trả lời tiếng Anh
- Tài liệu mixed (cả hai ngôn ngữ) → ưu tiên tiếng Việt

GROUNDING: Chỉ sử dụng thông tin từ nội dung tài liệu được cung cấp trong prompt. \
Không bổ sung từ kiến thức bên ngoài. \
Nếu câu hỏi không có câu trả lời trong tài liệu → nói rõ "Thông tin này không có trong tài liệu."

ĐỊNH DẠNG: Dùng Markdown để cấu trúc output khi hữu ích:
- ## hoặc ### cho chủ đề lớn (trong summary)
- **bold** cho khái niệm quan trọng
- - bullet list cho điểm liệt kê
- Không dùng Markdown cho câu trả lời ngắn (1-2 câu)

PHONG CÁCH: Học thuật, súc tích. Không thêm lời mở đầu sáo rỗng \
("Tất nhiên!", "Dưới đây là...", "Tôi rất vui được giúp...") \
hay lời kết thúc không cần thiết ("Hy vọng hữu ích!", "Tóm lại,").
```

**Giải thích từng dòng:**
- Persona ngắn — đủ để model biết context, không over-explain
- Language rule có 3 case cụ thể — không chỉ "match document language" mơ hồ
- Grounding có negative example ("Không bổ sung") + fallback phrase cụ thể ("Thông tin này không có trong tài liệu")
- Format có "khi hữu ích" + "Không dùng Markdown cho câu ngắn" — tránh over-formatting
- Anti-filler list các phrase cụ thể — model biết chính xác cái gì cần tránh

---

### `_SYSTEM_JSON` — Dùng cho Keywords, Relevance, Time Plan, KG

```
Bạn là trợ lý học thuật của FDocs — ứng dụng giúp sinh viên đọc tài liệu học thuật.

## Nguyên tắc

OUTPUT: Trả về ĐÚNG định dạng JSON như mô tả trong prompt. \
Không thêm text, markdown, code fence (```json), hay giải thích nào bên ngoài JSON. \
JSON phải là minified (không có whitespace thừa).

NGÔN NGỮ: Phát hiện ngôn ngữ chủ đạo từ nội dung tài liệu được cung cấp. \
Các trường text trong JSON (label, explanation, title, relation) phải dùng ngôn ngữ đó. \
Ưu tiên tiếng Việt nếu tài liệu mixed.

GROUNDING: Chỉ sử dụng thông tin từ nội dung tài liệu được cung cấp. \
Không bổ sung từ kiến thức bên ngoài.
```

**Giải thích từng dòng:**
- "Không thêm code fence" — `_strip_fences` vẫn giữ lại như safeguard, nhưng instruction này giảm frequency
- "Minified JSON" — best practice Google khuyến nghị, tiết kiệm token output
- Language rule list cụ thể các field cần match (`label`, `explanation`, `title`, `relation`) — model biết đích xác áp dụng ở đâu
- Grounding ngắn hơn `_SYSTEM_TEXT` — JSON features ít risk hallucination hơn (structured output constraint)

---

## User-Turn Prompt Improvements

Những thay đổi này là **bổ sung** cho system instruction, không thay thế:

### Summary — Map Step

```python
# Thay:
f"Summarize the following text concisely:\n\n{segment}"

# Thành:
f"Tóm tắt phần sau của tài liệu học thuật.\n"
f"Dùng ## heading cho các chủ đề lớn, bullet list (- item) cho điểm chính.\n\n"
f"{segment}"
```

### Summary — Reduce Step

```python
# Thay:
f"Synthesize these partial summaries into one coherent summary:\n\n{combined}"

# Thành:
f"Tổng hợp các tóm tắt sau thành một bản tóm tắt hoàn chỉnh và mạch lạc.\n"
f"Giữ cấu trúc ## heading cho các chủ đề lớn. Loại bỏ thông tin trùng lặp.\n\n"
f"{combined}"
```

### Q&A — answer_question + answer_question_stream

```python
# Thay:
f"Answer the question based ONLY on the provided context. "
f"If the answer is not in the context, say so.\n\n"
f"Context:\n{context}\n\n"
f"Question: {question}"

# Thành:
f"Trả lời câu hỏi dựa CHỈ VÀO ngữ cảnh được cung cấp dưới đây.\n"
f"Nếu câu trả lời không có trong ngữ cảnh, nói rõ: \"Tài liệu không đề cập đến điều này.\"\n"
f"Trích dẫn phần liên quan bằng cách dùng **bold** nếu hữu ích.\n\n"
f"Ngữ cảnh:\n{context}\n\n"
f"Câu hỏi: {question}"
```

### Relevance — Explanation Field

```python
# Thay trong prompt:
f"\"explanation\": \"<1-2 sentences>\""

# Thành:
f"\"explanation\": \"<2-3 câu phân tích. Dùng **bold** cho lý do điểm số cao/thấp>\""
```

---

## Đánh Giá Độ Rủi Ro

| Thay đổi | Risk | Lý do |
|---|---|---|
| Thêm `_SYSTEM_TEXT` | Thấp | System instruction không override JSON schema |
| Thêm `_SYSTEM_JSON` | Thấp | Reinforces existing "Return ONLY JSON" user-turn instruction |
| Summary prompt (map) | Thấp | Thêm format guidance, không đổi logic |
| Summary prompt (reduce) | Thấp | Như trên |
| Q&A prompt | Trung bình | Thay đổi ngôn ngữ prompt → cần verify test Q&A không bị regression |
| Relevance explanation | Thấp | Thay đổi string field mô tả, JSON structure không đổi |

**Q&A là thay đổi có risk cao nhất** vì `answer_question_stream` không retry được — nếu model không hiểu prompt mới thì không có fallback. Cần manual test sau khi implement.

---

## Thứ Tự Ưu Tiên Implement

| # | Task | Priority | Impact |
|---|---|---|---|
| 1 | Thêm `_SYSTEM_TEXT` + `_SYSTEM_JSON` constants | **P0** | Giải quyết ngôn ngữ + JSON tension ngay |
| 2 | Sửa factory functions (optional param) | **P0** | Enable system instruction |
| 3 | Gán đúng system instruction cho từng function | **P0** | Keywords/Relevance/TimePlan dùng `_SYSTEM_JSON` |
| 4 | Cải thiện Summary prompts (map + reduce) | **P1** | Cải thiện format output rõ thấy nhất |
| 5 | Cải thiện Q&A prompts | **P2** | Sau khi P0+P1 stable, manual test trước khi deploy |
| 6 | Relevance explanation field | **P2** | Nhỏ, đi kèm với P2 Q&A |

---

## Action Items cho Backend Worker

1. **[P0]** Thêm 2 constants `_SYSTEM_TEXT` và `_SYSTEM_JSON` vào `gemini_service.py` (đặt trước `_make_client`)
2. **[P0]** Sửa `_make_client(api_key, system_instruction=_SYSTEM_TEXT)` — thêm optional param, default = `_SYSTEM_TEXT`
3. **[P0]** Sửa `_make_json_client(api_key, schema, system_instruction=_SYSTEM_JSON)` — thêm optional param, default = `_SYSTEM_JSON`
4. **[P0]** Sửa call-sites trong `extract_keywords`, `score_relevance`, `generate_time_plan`: `_make_client(api_key, system_instruction=_SYSTEM_JSON)`
   - `generate_summary` và `answer_question*` dùng default (`_SYSTEM_TEXT`) — không cần sửa
5. **[P1]** Sửa user-turn prompts trong `generate_summary` (map step + reduce step)
6. **[P2]** Sửa user-turn prompts trong `answer_question` và `answer_question_stream` (cùng lúc, 2 hàm dùng cùng pattern)
7. **[P2]** Sửa explanation description string trong `score_relevance`

**Test sau khi implement P0:**
- Chạy `pytest backend/` — verify 113 tests pass (unit tests đã mock, không ảnh hưởng)
- Manual: upload tài liệu tiếng Việt → generate summary → verify tiếng Việt + có heading/bullet
- Manual: upload tài liệu tiếng Anh → verify summary tiếng Anh

**Test sau khi implement P2 (Q&A):**
- Manual: hỏi câu có trong tài liệu → verify trả lời đúng ngôn ngữ
- Manual: hỏi câu không có trong tài liệu → verify model nói "Tài liệu không đề cập" thay vì bịa

---

## Sources

- [Prompt design strategies | Gemini API | Google AI for Developers](https://ai.google.dev/gemini-api/docs/prompting-strategies)
- [Gemini System Instructions — Examples, Templates & Best Practices 2026 | Brainfile](https://brainfile.io/gemini-system-instructions)
- [Structured Output with Gemini | Google AI Developers](https://ai.google.dev/gemini-api/docs/structured-output)
- [Caching | Gemini API | Google AI for Developers](https://ai.google.dev/api/caching)
- [Mastering the Art of Prompting LLMs for RAG | Progress](https://www.progress.com/blogs/mastering-the-art-of-prompting-llms-for-rag)
- [LLM Grounding Leads to More Accurate Contextual Responses | k2view](https://www.k2view.com/blog/llm-grounding/)
- [Smarter Prompts: Engineering Better Instructions in RAG | Medium](https://medium.com/@ai.nishikant/smarter-prompts-engineering-better-instructions-in-rag-58e87ad8077f)
- [Mitigating Hallucinations in Zero-Shot Scientific Summarisation](https://arxiv.org/pdf/2512.00931)
