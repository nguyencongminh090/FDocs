# FDocs — API Reference

> Base URL: `http://localhost:8000`  
> Auth: `Authorization: Bearer <access_token>`  
> BYOK: `X-Gemini-Key: <user_gemini_key>` (bắt buộc với mọi endpoint gọi AI)

---

## Auth

### POST /api/auth/register
Đăng ký tài khoản mới. Trả về access token + set httpOnly cookie `refresh_token`.

**Body**
```json
{ "email": "user@example.com", "password": "min8chars" }
```
**Response 201**
```json
{ "access_token": "...", "token_type": "bearer", "user": { "id": "uuid", "email": "...", "created_at": "..." } }
```

---

### POST /api/auth/login
**Body**: `{ "email": "...", "password": "..." }`  
**Response 200**: `{ "access_token": "...", "token_type": "bearer" }`  
Set-Cookie: `refresh_token` (httpOnly)

---

### POST /api/auth/refresh
Dùng cookie `refresh_token` để lấy access token mới.  
**Response 200**: `{ "access_token": "...", "token_type": "bearer" }`

---

### POST /api/auth/logout
Xóa refresh token trên server + xóa cookie.  
**Auth required** | **Response 204**

---

## Documents

### POST /api/documents
Upload metadata + extracted text. Backend tự chunk + embed.  
**Auth + X-Gemini-Key required**

**Body**
```json
{
  "title": "Giáo trình Đại số tuyến tính",
  "file_type": "pdf",
  "word_count": 45000,
  "page_count": 180,
  "extracted_text": "..."
}
```
**Response 201**: `DocumentResponse`

---

### GET /api/documents
Lấy danh sách tài liệu của user (không có `extracted_text`).  
**Auth required** | **Response 200**: `DocumentResponse[]`

---

### GET /api/documents/{doc_id}
Lấy chi tiết tài liệu bao gồm `extracted_text`.  
**Auth required** | **Response 200**: `DocumentDetailResponse`

---

### DELETE /api/documents/{doc_id}
Xóa tài liệu và toàn bộ dữ liệu liên quan (cascade).  
**Auth required** | **Response 204**

---

## Analysis (Read Mode)

Tất cả endpoint analysis đều cần **Auth + X-Gemini-Key**.

### GET /api/documents/{doc_id}/analysis
Lấy toàn bộ kết quả đã lưu (summary, keywords, relevance, time_plan, kg).  
**Response 200**: `AnalysisResultResponse | null`

---

### POST /api/documents/{doc_id}/analyze/summary
Tạo tóm tắt hierarchical (chunk → partial → final).  
**Response 200**: `{ "summary": "..." }`

---

### POST /api/documents/{doc_id}/analyze/keywords
Trích xuất 10-15 từ khóa quan trọng.  
**Response 200**: `{ "keywords": ["...", "..."] }`

---

### POST /api/documents/{doc_id}/analyze/relevance
Đánh giá độ phù hợp tài liệu với nhu cầu người dùng.

**Body**
```json
{ "goal": "...", "keywords": ["...", "..."], "topic": "..." }
```
**Response 200**: `{ "relevance_score": 0.82, "explanation": "..." }`

---

### POST /api/documents/{doc_id}/analyze/time-plan
Lên kế hoạch đọc theo ngày.

**Body**
```json
{ "start_date": "2026-06-20", "deadline": "2026-07-10", "hours_per_day": 2 }
```
**Response 200**: `{ "time_plan": [{ "date": "2026-06-20", "sessions": [{ "title": "Chương 1", "estimated_minutes": 60 }] }] }`

---

### POST /api/documents/{doc_id}/analyze/knowledge-graph
Tạo knowledge graph từ nội dung tài liệu.  
**Response 200**:
```json
{
  "kg": {
    "nodes": [{ "id": "n1", "label": "Linear Algebra", "type": "concept" }],
    "edges": [{ "source": "n1", "target": "n2", "relation": "includes" }]
  }
}
```

---

### GET /api/documents/{doc_id}/related
Gợi ý top-3 tài liệu tương đồng nhất trong library dựa trên embedding similarity.  
**Auth + X-Gemini-Key** | **Response 200**: `RelatedDocResponse[]`

---

## Q&A (Understand Mode)

### POST /api/documents/{doc_id}/qa
Đặt câu hỏi, AI trả lời dựa trên RAG (không streaming).  
**Auth + X-Gemini-Key required**

**Body**: `{ "question": "..." }`  
**Response 200**: `QAResponse`

---

### POST /api/documents/{doc_id}/qa/stream
Đặt câu hỏi, AI trả lời dạng SSE stream (typewriter effect).  
**Auth + X-Gemini-Key required**

**Body**: `{ "question": "..." }`  
**Response**: `text/event-stream`

Mỗi chunk: `data: <JSON-encoded-string>\n\n`  
Kết thúc thành công: `data: [DONE]\n\n`

Lỗi giữa stream (status HTTP 200 đã commit nên không đổi được status): server phát **error frame** in-band rồi đóng stream, **không** có `[DONE]`:
```
data: {"error": "quota", "detail": "..."}\n\n     # vượt quota Gemini
data: {"error": "service", "detail": "..."}\n\n   # lỗi Gemini khác
data: {"error": "server", "detail": "..."}\n\n    # lỗi máy chủ
```
Client phải dùng `fetch` (không phải `EventSource`) để gửi được custom headers, và phải xử lý cả `[DONE]` lẫn frame `error`.  
Câu trả lời chỉ được lưu vào `qa_history` **khi stream hoàn tất trọn vẹn** — stream lỗi/đứt giữa chừng không lưu câu trả lời dở.

---

### GET /api/documents/{doc_id}/qa
Lấy lịch sử Q&A của tài liệu.  
**Auth required** | **Response 200**: `QAResponse[]`

---

## Library

### GET /api/library/similarity-map
Lấy đồ thị tương đồng giữa tất cả tài liệu trong library của user.  
**Auth required**

**Response 200**:
```json
{
  "nodes": [
    { "id": "uuid", "title": "...", "word_count": 12500, "file_type": "pdf" }
  ],
  "edges": [
    { "source": "uuid", "target": "uuid", "similarity": 0.82 }
  ]
}
```

- Edges chỉ được trả về khi `similarity >= 0.65`
- Documents chưa có chunks (chưa embed) sẽ không xuất hiện trong nodes
- Dùng centroid embedding (avg của tất cả chunks) để tính cosine similarity theo cặp

---

## Common Response Types

```typescript
DocumentResponse {
  id: string (UUID)
  title: string
  file_type: "pdf" | "docx"
  word_count: number | null
  page_count: number | null
  sections: object | null
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}

QAResponse {
  id: string (UUID)
  question: string
  answer: string
  sources: [{ chunk_id: string, chunk_index: number, excerpt: string }] | null
  created_at: string (ISO 8601)
}
```

---

## Error Responses

| Status | Tình huống |
|---|---|
| 400 | Validation lỗi, thiếu X-Gemini-Key |
| 401 | Token không hợp lệ hoặc hết hạn |
| 404 | Document không tồn tại hoặc không thuộc user |
| 409 | Email đã được đăng ký |
| 429 | Vượt quota / rate limit Gemini API (free tier) — đã retry backoff nhưng vẫn bị chặn. Thử lại sau ít phút hoặc dùng tài liệu nhỏ hơn |
| 502 | Gemini API lỗi (không phải quota): JSON trả về không hợp lệ, nội dung bị bộ lọc an toàn chặn, hoặc lỗi dịch vụ |
| 500 | Lỗi server nội bộ ngoài dự kiến |

Tất cả lỗi trả về: `{ "detail": "..." }`

**Lưu ý mọi endpoint gọi AI** (documents POST, analyze/*, qa, related): lỗi quota Gemini nhất quán trả **429**, lỗi Gemini khác trả **502** (trước đây một số path rò thành 500). Với endpoint SSE (`qa/stream`), lỗi sau khi stream đã bắt đầu được phát dưới dạng error frame in-band (xem mục Q&A), không phải HTTP status.
