# FDocs

> Trợ lý đọc tài liệu bằng AI, giúp sinh viên đọc — hiểu — lĩnh hội tri thức từ tài liệu học thuật dài, dựa trên RAG (Retrieval-Augmented Generation) và Google Gemini API.

🇻🇳 Tiếng Việt · 🇬🇧 [English (default)](README.md)

---

## 📖 FDocs là gì?

FDocs biến một file PDF/DOCX dày đặc (giáo trình, bài báo, slide) thành thứ sinh viên có thể thực sự xử lý được. Bạn tải tài liệu lên, dùng Gemini API key của chính mình, và FDocs phủ lên đó một lớp đọc thông minh: tóm tắt, bản đồ từ khóa, đánh giá độ phù hợp trước khi đọc, knowledge graph, kế hoạch đọc, và chat Hỏi-Đáp **chỉ trả lời dựa trên tài liệu**.

## 💡 Ý tưởng

Sinh viên ngợp trong tài liệu dài và phức tạp dưới áp lực deadline. Tư tưởng cốt lõi của FDocs:

- **Quyết định trước khi đọc** — chấm độ phù hợp của tài liệu với *mục tiêu của bạn* trước.
- **Đọc có cấu trúc** — tóm tắt, từ khóa, knowledge graph cho bạn thấy "hình dạng" nội dung trước khi đi vào chi tiết.
- **Hỏi thay vì dò** — chat RAG trả lời câu hỏi dựa trên tài liệu, kèm trích dẫn đoạn nguồn, thay vì bạn phải lật 50 trang.
- **Key của bạn, dữ liệu của bạn** — BYOK (Bring Your Own Key): Gemini key nằm trong trình duyệt, file gốc được parse tại máy, không upload lên server.

## 🌱 Ý nghĩa / đóng góp

- **Ưu tiên riêng tư**: tài liệu được parse ngay trên trình duyệt (pdf.js + mammoth.js); chỉ phần text trích xuất được gửi lên server; API key không bao giờ bị lưu/log phía server.
- **Bám tài liệu theo thiết kế**: pipeline Hỏi-Đáp dùng hybrid retrieval (semantic + lexical) và prompt từ chối bịa thông tin ngoài tài liệu — giảm hallucination mà vẫn hữu ích.
- **Mở & mang tính học tập**: một ứng dụng RAG hoàn chỉnh đầu-cuối (FastAPI + pgvector + Gemini + React) để người khác đọc, học và mở rộng.

## ✨ Tính năng

| Mảng | Tính năng |
|---|---|
| **Tải lên** | PDF / DOCX parse **tại trình duyệt**; chỉ gửi text lên server; tiến trình upload realtime (SSE) |
| **Chế độ Đọc** | Tóm tắt phân cấp · trích xuất từ khóa · điểm độ phù hợp (so với mục tiêu) · tài liệu liên quan · kế hoạch đọc |
| **Chế độ Hiểu sâu** | **Knowledge graph** tương tác · **Chat Hỏi-Đáp** (RAG, bám tài liệu, streaming) |
| **Chất lượng Hỏi-Đáp** | Hybrid retrieval (semantic cosine + lexical full-text, fuse bằng RRF) + prompt 3 trạng thái (trả lời / một phần / từ chối) |
| **Hiển thị** | Markdown + LaTeX (KaTeX) trong output AI |
| **Tài khoản & cài đặt** | Xác thực JWT · tùy chọn ngôn ngữ (Auto/VI/EN) · quản lý Gemini key (BYOK) |

## 🧱 Công nghệ

- **Frontend**: React 19, Vite, Tailwind CSS, React Router, Cytoscape (graph), KaTeX, pdf.js, mammoth.js
- **Backend**: FastAPI, SQLAlchemy (async), LangChain, `google-generativeai`
- **Database**: PostgreSQL + **pgvector** (`gemini-embedding-001`, 768 chiều)
- **AI**: Google Gemini (`gemini-2.5-flash` sinh nội dung + `gemini-embedding-001`)
- **Hạ tầng**: Docker Compose, GitHub Actions (CI), Nginx (phục vụ frontend)

---

## 🚀 Cài đặt (từng bước)

### Yêu cầu
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- Một **Google Gemini API key** (free tier là đủ) — lấy tại [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone
```bash
git clone https://github.com/nguyencongminh090/FDocs.git
cd FDocs
```

### 2. Tạo file `.env` (thư mục gốc)
```env
# Postgres
POSTGRES_USER=fdocs
POSTGRES_PASSWORD=doi-mat-khau

# Backend
DATABASE_URL=postgresql+asyncpg://fdocs:doi-mat-khau@db:5432/fdocs
SECRET_KEY=thay-bang-ket-qua-cua-`openssl rand -hex 32`
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
ALLOWED_ORIGINS=http://localhost:3000

# Cổng frontend
PORT=3000
```
> ⚠️ Dùng **service host `db`** (không phải `localhost`) trong `DATABASE_URL` — đó là tên trong mạng Docker. Tạo secret thật bằng `openssl rand -hex 32`.

### 3. Build & chạy
```bash
docker compose up --build -d
```
Lệnh này khởi động 3 container: `db` (Postgres + pgvector, schema tự áp từ `backend/migrations/`), `backend` (FastAPI), `frontend` (Nginx).

### 4. Lần đầu dùng
1. Mở app (xem bên dưới), **đăng ký** tài khoản.
2. Vào **Cài đặt → Gemini API Key**, dán key của bạn (chỉ lưu trong trình duyệt).
3. Tải PDF/DOCX lên và bắt đầu đọc.

### Chạy dev (không Docker, tùy chọn)
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000

# Frontend
cd frontend && npm install
npm run dev                            # http://localhost:5173
```
> Trình quản lý gói chuẩn của dự án là **npm** (CI và Docker dùng `npm ci`). Nếu đổi dependency, nhớ commit `package-lock.json` đã cập nhật.

---

## 🌐 Truy cập site

Hiện chưa có bản deploy công khai (xem Roadmap). Sau khi `docker compose up`:

| Dịch vụ | URL |
|---|---|
| **Web app** | `http://localhost:3000` (hoặc `PORT` của bạn) |
| Backend API | `http://localhost:8000` |
| Tài liệu API (Swagger) | `http://localhost:8000/docs` |

---

## 🗺️ Lộ trình / sắp tới

- [ ] **Deploy production** — GitHub Actions deploy qua SSH (secrets + file `.env` trên server)
- [ ] **Mở rộng multi-worker** — job store upload hiện in-memory (1 worker); chuyển sang Redis làm job bus dùng chung
- [ ] **Re-rank Hỏi-Đáp (giai đoạn 3)** — cross-encoder re-rank / HyDE nếu hybrid chưa đủ
- [ ] **Bộ đánh giá Hỏi-Đáp tự động** — đo false-positive & độ trung thực theo thời gian
- [ ] Tóm tắt async toàn văn cho tài liệu rất dài

## ⚖️ Ưu & nhược điểm

**Điểm mạnh**
- Ưu tiên riêng tư (BYOK); file gốc không rời khỏi trình duyệt.
- Hỏi-Đáp RAG bám tài liệu, hybrid retrieval — mạnh trước hallucination.
- Tự host chỉ bằng một lệnh `docker compose up`.
- Hiển thị Markdown + LaTeX, phù hợp tài liệu STEM.

**Hạn chế (thành thật)**
- **Quota Gemini free-tier**: tài liệu dài có thể chạm giới hạn (HTTP 429) khi embedding/tóm tắt.
- **Pipeline upload 1 worker**: tiến trình SSE dựa trên job store in-memory — chưa an toàn khi chạy nhiều worker.
- **Chưa có demo / deploy công khai**.
- **Hỏi-Đáp chưa đo định lượng** — mới kiểm bằng UAT người thật, chưa có bộ metric tự động.
- Lexical search chạy on-the-fly (chưa có index full-text) — đủ cho từng tài liệu, chưa tối ưu cho corpus lớn.
- Full-text tiếng Việt dùng config `simple` (không stemming).

---

## 🤝 Đóng góp

Rất hoan nghênh đóng góp — codebase thân thiện cho người học.

1. Fork & tạo branch từ `main` (`feat/...` hoặc `fix/...`); **không commit thẳng vào `main`**.
2. Mỗi commit một thay đổi logic; message dạng `type(scope): mô tả` (vd `feat(qa): ...`).
3. Chạy test trước khi mở PR: `npm test` (frontend) và `pytest` (backend, cần dev deps).
4. Mở PR lên `main` kèm mô tả ngắn + ghi chú test.

Xem thư mục `docs/` cho PRD, schema, API và các quyết định thiết kế.

## 🎯 Mong muốn

Chúng mình hy vọng FDocs khiến những tài liệu khó bớt đáng sợ hơn — để sinh viên đỡ tốn thời gian lật trang và dành nhiều thời gian hơn để thực sự hiểu. Nếu nó giúp bạn đọc thông minh hơn, vậy là đạt mục tiêu. ⭐ Star repo, mở issue, hoặc gửi PR nhé.

## 📄 Giấy phép

Giấy phép: chưa quyết định (do team thống nhất sau).
