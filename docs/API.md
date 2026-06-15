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
Đặt câu hỏi, AI trả lời dựa trên RAG.  
**Auth + X-Gemini-Key required**

**Body**: `{ "question": "..." }`  
**Response 200**: `QAResponse`

---

### GET /api/documents/{doc_id}/qa
Lấy lịch sử Q&A của tài liệu.  
**Auth required** | **Response 200**: `QAResponse[]`

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
| 500 | Lỗi server hoặc Gemini API thất bại |

Tất cả lỗi trả về: `{ "detail": "..." }`
