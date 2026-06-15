# FDocs — Product Requirements Document

> **Trạng thái**: v1.3 — **APPROVED** — Sẵn sàng chuyển giao cho Database Worker  
> **Cập nhật lần cuối**: 2026-06-15  
> **Product Manager**: AI Agent

---

## Goal

Xây dựng web application hỗ trợ sinh viên đọc, hiểu và lĩnh hội tri thức từ tài liệu học thuật dài và phức tạp (sách, bài báo, giáo trình) một cách hiệu quả và có hệ thống — thông qua AI (Google Gemini API) kết hợp RAG pipeline.

---

## Target Users

**Sinh viên đại học/sau đại học** cần xử lý lượng lớn tài liệu học thuật trong thời gian có hạn.

**Pain points cụ thể:**
- Không biết tài liệu có phù hợp với nhu cầu trước khi đọc toàn bộ
- Mất nhiều thời gian đọc tài liệu dài mà không có kế hoạch rõ ràng
- Khó nắm bắt mối liên hệ giữa các khái niệm trong tài liệu phức tạp

---

## Core Features (P0)

### 1. BYOK — Bring Your Own Key
- User nhập Gemini API key cá nhân của họ
- Key lưu `localStorage` → gửi qua HTTPS header mỗi request → backend gọi Gemini → không log/lưu key trên server
- UI hướng dẫn user cách lấy Gemini API key (link đến Google AI Studio)

### 2. Upload & Parse Tài Liệu
- Định dạng hỗ trợ: PDF, DOCX
- Parse tại browser (pdf.js + mammoth.js) — file gốc **không upload lên server**
- Chỉ gửi extracted text lên backend để lưu metadata
- Hiển thị preview nội dung sau khi parse thành công

### 3. Read Mode — Đọc Thông Minh

| Tính năng | Mô tả |
|---|---|
| **Tóm tắt** | Hierarchical summary: chunk → summarize từng chunk → tổng hợp |
| **Keywords** | AI trích xuất danh sách từ khóa và khái niệm chính |
| **Relevance Score** | Đánh giá độ phù hợp tài liệu với nhu cầu người dùng nhập qua form có cấu trúc |
| **Related Docs** | Gợi ý tài liệu liên quan từ library cá nhân đã upload |
| **Time Plan** | Lên kế hoạch đọc dựa trên form: ngày bắt đầu, deadline, số giờ/ngày |

#### Relevance Score — Input Form

User nhập nhu cầu qua form 3 trường có cấu trúc:

| Trường | Loại Input | Ví dụ |
|---|---|---|
| **Goal** | Textarea | "Nắm kiến thức về toán đại số tuyến tính" |
| **Keywords** | Tag input (gõ + Enter) | `Linear Algebra`, `Vectorization`, `Linear Regression` |
| **Topic** | Text input | "Linear Algebra" |

Backend dùng `Goal` để embedding match, `Keywords` để keyword scoring, `Topic` để classify.

#### Time Plan — Input Form

| Trường | Loại Input |
|---|---|
| Ngày bắt đầu | Date picker |
| Deadline | Date picker |
| Số giờ/ngày có thể đọc | Number input (giờ) |

Output: danh sách session đọc theo ngày, mỗi session gồm phần/chương cần đọc.

### 4. Understand Mode — Hiểu Sâu

| Tính năng | Mô tả |
|---|---|
| **Knowledge Graph** | Tạo đồ thị khái niệm từ nội dung tài liệu, render interactive |
| **Q&A (RAG)** | Người dùng đặt câu hỏi, AI trả lời dựa hoàn toàn trên context tài liệu |

### 5. Auth & Library
- Đăng ký / Đăng nhập tài khoản (email + password)
- Mỗi user có library riêng gồm metadata các tài liệu đã xử lý
- Lưu kết quả: summary, keywords, KG, Q&A history theo từng tài liệu

---

## Out of Scope (v1)

- Kết nối external knowledge base (Wikipedia, Semantic Scholar, v.v.)
- Real-time collaboration nhiều người trên cùng tài liệu
- Mobile app (chỉ web, desktop-first)
- Export file kết quả (PDF/DOCX)
- Tích hợp calendar app bên ngoài
- Server-side file storage (file gốc không lưu trên server)

---

## Tech Stack (Đã xác nhận)

| Layer | Công nghệ | Ghi chú |
|---|---|---|
| **Frontend** | React + Vite | |
| **LLM Provider** | Google Gemini API | BYOK — user tự cung cấp key |
| **LLM Framework** | LangChain (Python) | RAG pipeline, KG extraction |
| **RAG** | LangChain RAG pipeline | Chunking + embedding + vector store + retrieve |
| **KG Visualization** | Cytoscape.js | |
| **PDF Parsing** | pdf.js (browser) | Client-side, không upload file gốc |
| **DOCX Parsing** | mammoth.js (browser) | Client-side |
| **Backend** | Python FastAPI | Auth + metadata API + Gemini proxy |
| **Database** | PostgreSQL + pgvector extension | pgvector cho embedding similarity search |
| **Auth** | JWT — access token 15 phút, refresh token httpOnly cookie | |

---

## Architecture Overview

```
[Browser]
  ├── pdf.js / mammoth.js  → extract text từ file (file không rời browser)
  ├── React UI
  └── BYOK key → localStorage

[HTTPS Requests]
  └── Authorization: Bearer <jwt>
      X-Gemini-Key: <user_api_key>  ← không log, không lưu

[FastAPI Backend]
  ├── Auth API (JWT)
  ├── Document metadata API (lưu extracted text + kết quả AI)
  ├── Gemini Proxy (nhận key từ header, gọi Gemini, trả kết quả)
  └── LangChain RAG pipeline (chunking, embedding, retrieve, generate)

[PostgreSQL]
  ├── users
  ├── documents  (metadata + extracted_text + chunks)
  ├── analysis_results  (summary, keywords, relevance, time_plan, kg)
  └── qa_history
```

---

## RAG Pipeline (Chi tiết)

```
extracted_text
  → chunking (LangChain TextSplitter, ~512 tokens/chunk, 50 token overlap)
  → embedding (Gemini text-embedding-004)
  → vector store (pgvector)
  → [Query] → retrieve top-k chunks
  → [Context + Query] → Gemini generate → response
```

Dùng cho: Q&A, Relevance Score, Related Docs suggestion.

**Related Docs**: Tính cosine similarity giữa embedding của tài liệu hiện tại và toàn bộ tài liệu trong library của user (stored trong pgvector). Top-3 tài liệu tương đồng nhất được gợi ý. ✅

Tóm tắt dùng Hierarchical approach (chunk → partial summary → final summary).

---

## KG Generation — Structured Output Strategy

Gemini hỗ trợ `response_mime_type: "application/json"` + `response_schema` → output luôn hợp lệ theo schema.

Schema KG:
```json
{
  "nodes": [{ "id": "string", "label": "string", "type": "concept|entity|process" }],
  "edges": [{ "source": "string", "target": "string", "relation": "string" }]
}
```

Fallback: nếu Gemini không tuân thủ schema → retry tối đa 2 lần → báo lỗi user.

---

## Non-Functional Requirements

- Parse tài liệu 20 trang: < 5 giây (browser)
- AI response (Q&A): < 10 giây
- Tóm tắt tài liệu dài: < 60 giây (có progress indicator)
- Hoạt động trên Chrome/Edge phiên bản mới nhất
- Responsive desktop-first (min-width: 1024px)
- File gốc tuyệt đối không lưu trên server

---

## Decisions Log

| # | Vấn đề | Quyết định |
|---|---|---|
| 1 | KG Visualization library | Cytoscape.js |
| 2 | Vector Store | pgvector (persistent, trong PostgreSQL) |
| 3 | Related Docs algorithm | Embedding similarity (cosine) giữa doc hiện tại và library |
| 4 | Chunks storage model | Bảng `chunks` riêng: `chunks(id, document_id, content, embedding vector(768), chunk_index)` — bắt buộc cho pgvector RAG retrieval |
| 5 | KG storage | JSONB blob trong column `kg` của `analysis_results` — đủ cho v1 vì Cytoscape.js load toàn bộ graph |
| 6 | Time Plan section detection | AI regex detect headings (`^#{1,3}`, `CHAPTER`, `Chương`, `\d+\.`) → fallback chia đều theo word count nếu không tìm được heading |
| 7 | Email verification | Bỏ qua v1 — login ngay sau register; thêm v2 nếu cần |
