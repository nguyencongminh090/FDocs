# FDocs — Progress Tracker

> Cập nhật lần cuối: 2026-06-17

---

## Phase 0 — Product Planning ✅ DONE

**Output artifacts:**
- `docs/PRD.md` v1.3 — APPROVED, sẵn sàng chuyển giao
- `docs/PROGRESS.md` (file này)

**Decisions chốt (v1.3):**
- Chunks: bảng `chunks` riêng với `embedding vector(768)`
- KG: JSONB blob trong `analysis_results.kg`
- Time Plan: regex heading detection + word count fallback
- Auth: không cần email verification ở v1

---

## Phase 1 — Database Schema ✅ DONE

**Worker**: Database Worker (`/as-db`)

**Tasks:**
- [x] Thiết kế ERD đầy đủ (Mermaid)
- [x] Viết SQL migration file (plain SQL)
- [x] Enable pgvector + pgcrypto extension
- [x] HNSW index trên `chunks.embedding` (cosine, m=16, ef_construction=64)
- [x] Auto-update trigger cho `updated_at`

**Output artifacts:**
- `docs/schema.md` — ERD + chi tiết từng bảng + index table
- `backend/migrations/0001_initial_schema.sql` — migration file đầy đủ

---

## Phase 2 — Backend API ✅ DONE

**Worker**: Backend Worker (`/as-backend`)

**Tasks:**
- [x] Cấu trúc FastAPI theo layer (routes / services / repositories / middlewares)
- [x] Auth: register, login, refresh, logout (JWT + httpOnly cookie)
- [x] Documents CRUD
- [x] Analysis: summary, keywords, relevance, time-plan, knowledge-graph, related-docs
- [x] Q&A RAG endpoint + lịch sử
- [x] Gemini service (chunk, embed, generate, KG structured output)
- [x] Error handler middleware + CORS config

**Output artifacts:**
- `backend/app/` — toàn bộ source code FastAPI
- `backend/requirements.txt`
- `backend/.env.example`
- `docs/API.md` — API reference đầy đủ

---

## Phase 3 — Frontend ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Tasks:**
- [x] Vite + React project init
- [x] Tailwind CSS + CSS variable 3-theme system (neutral / cream / dark)
- [x] ThemeProvider, AuthContext, GeminiKeyContext
- [x] API service layer với JWT auto-attach + Gemini Key header + auto-refresh
- [x] Auth pages: Login, Register, API Key Setup
- [x] AppLayout (sidebar + command palette ⌘K) + AuthLayout
- [x] Library page (grid view)
- [x] Upload page (drag-drop, pdf.js + mammoth.js, progress bar)
- [x] Document page: Read Mode (Summary, Keywords, Relevance, TimePlan, RelatedDocs)
- [x] Document page: Understand Mode (KnowledgeGraph Cytoscape + spring animation, Q&A streaming)
- [x] Command Palette ⌘K (cmdk)
- [x] Build verified: ✓ 2172 modules, no errors

**Output artifacts:**
- `frontend/` — toàn bộ React source code
- `docs/DESIGN_LOG.md` — design decisions + differentiation features log

**[DESIGN PENDING] items — ĐÃ RESOLVE:**
- Library Similarity Map (#2) — ✅ Design spec hoàn chỉnh trong DESIGN_LOG.md; chờ backend endpoint `GET /api/library/similarity-map`
- Reading Heatmap (#4) — ✅ Design spec hoàn chỉnh trong DESIGN_LOG.md; chờ backend update qa_history sources với chunk_index

---

## Phase 3b — Design Enhancement 🎨 DONE

**Worker**: Designer Worker (`/as-designer`)

**Tasks:**
- [x] Research benchmark apps (Readwise Reader, ReadCube Papers, Elicit, Notion, Linear)
- [x] Resolve 4 Open Design Questions (navigation, layout, split view, mobile)
- [x] Animation spec đầy đủ (18 animation types, shimmer skeleton, focus mode)
- [x] Semantic color tokens (success/warning/error/info + dark variants)
- [x] Library Similarity Map — UX/interaction spec hoàn chỉnh
- [x] Reading Heatmap — UX/interaction spec + implementation approach
- [x] Component state spec (Button, Input, Card)
- [x] Accessibility spec (WCAG AA, focus-visible, aria-label, KG table fallback)
- [x] Frontend handoff checklist (P0 + P1)

**Output artifacts:**
- `docs/DESIGN_LOG.md` — full spec, handoff checklist, all decisions logged

---

## Phase 3c — Frontend Design Enhancement ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Tasks:**
- [x] Semantic color tokens (success/warning/error/info) cho cả 3 theme trong `index.css`
- [x] Theme switch transition (`background-color, color, border-color 200ms ease-in-out`) trên `*`
- [x] Shimmer skeleton animation (`@keyframes shimmer`, `.skeleton` class) — thay `animate-pulse`
- [x] `SummaryPanel`: dùng `.skeleton` với deterministic widths (bỏ `Math.random`)
- [x] `KeywordsPanel`: shimmer loading + stagger animation 40ms/tag khi kết quả load
- [x] Page mount animation (`@keyframes fadeSlideUp`, `.animate-page-in`) trên DocumentPage
- [x] Keyword tag animation (`@keyframes tagIn`, `.animate-tag-in`)
- [x] Sidebar collapse: toggle button + `\` shortcut, persist localStorage, icon-only 56px mode
- [x] Split-view layout trong DocumentPage: Text panel (42%) + Tools panel (58%)
- [x] Text panel toggle: button `[AlignLeft]` trong header, hide/show với state
- [x] Focus mode: phím `F` / button `[Focus]` → ẩn sidebar + center tools panel; `Esc` để thoát
- [x] Button press animation: `active:scale-[0.97]` + `hover:-translate-y-px`
- [x] Card clickable hover: `-translate-y-0.5 + shadow-md` khi có `onClick`
- [x] `prefers-reduced-motion` wrapper trong `index.css`
- [x] Error messages dùng `var(--error)` thay vì `text-red-500` hardcode
- [x] Build verified: ✓ 2172 modules, 0 errors

**Output artifacts:**
- `frontend/src/index.css` — full rewrite với semantic tokens + animations
- `frontend/src/layouts/AppLayout.jsx` — sidebar collapse + focusMode context
- `frontend/src/features/document/DocumentPage.jsx` — split view + focus mode
- `frontend/src/features/document/read-mode/SummaryPanel.jsx` — shimmer skeleton
- `frontend/src/features/document/read-mode/KeywordsPanel.jsx` — shimmer + stagger
- `frontend/src/components/ui/Button.jsx` — press + hover animation
- `frontend/src/components/ui/Card.jsx` — clickable hover animation

---

## Phase 2b — Backend Enhancement ✅ DONE

**Worker**: Backend Worker (`/as-backend`)

**Tasks:**
- [x] `POST /api/documents/{doc_id}/qa/stream` — SSE streaming endpoint (FastAPI StreamingResponse)
- [x] `answer_question_stream` async generator trong `gemini_service.py` (Gemini `stream=True`)
- [x] `ask_stream_response` trong `qa_service.py` — embed → retrieve → stream → save to DB
- [x] Data format: JSON-encoded tokens (`data: "text"\n\n`) + `data: [DONE]\n\n`
- [x] `GET /api/library/similarity-map` — all-pairs cosine similarity giữa doc centroids
- [x] `get_all_doc_centroids` trong `ChunkRepository` (SQL avg embedding + JOIN documents)
- [x] `LibraryService` với pure-Python cosine similarity, threshold 0.65
- [x] `library.py` route registered trong `main.py`
- [x] Fix `frontend/src/services/qa.js` — thay `EventSource` bằng `fetch` + `ReadableStream`
  - `EventSource` không hỗ trợ custom headers → không truyền được JWT + Gemini Key
  - `fetch`-based SSE: gửi `Authorization` + `X-Gemini-Key` đúng cách
- [x] `getAuthToken()` export từ `api.js` để `qa.js` lấy access token từ memory
- [x] `docs/API.md` cập nhật với 2 endpoint mới
- [x] Build verified: ✓ frontend build pass sau khi thay đổi

**Output artifacts:**
- `backend/app/services/gemini_service.py` — thêm `answer_question_stream`
- `backend/app/services/qa_service.py` — thêm `ask_stream_response`
- `backend/app/routes/qa.py` — thêm `POST /stream` route
- `backend/app/repositories/chunk_repository.py` — thêm `get_all_doc_centroids`, bỏ unused import
- `backend/app/services/library_service.py` — file mới
- `backend/app/routes/library.py` — file mới
- `backend/app/main.py` — register library router
- `frontend/src/services/qa.js` — fix streamAsk sang fetch-based SSE
- `frontend/src/services/api.js` — export `getAuthToken`
- `docs/API.md` — documented 2 endpoints mới

---

## Phase 3d — Library Map View ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Tasks:**
- [x] `documentService.getSimilarityMap()` — gọi `GET /api/library/similarity-map`
- [x] `LibrarySimilarityMap.jsx` — Cytoscape component với full spec từ DESIGN_LOG:
  - Node: circle 64px, opacity theo word_count (nhiều từ → đậm hơn)
  - Edge: hiện khi similarity ≥ 0.65, thickness linear 1–4px theo similarity score
  - COSE layout với spring animation (1200ms)
  - Theme-aware colors (neutral / cream / dark)
  - Hover node: ring highlight + floating tooltip (DOM ref, không re-render)
  - Hover: connected edges highlight, others dimmed (opacity 0.1)
  - Click node: navigate to document
  - Empty state < 2 docs: message
  - No edges state: overlay message
- [x] `LibraryPage.jsx` — hybrid view toggle:
  - Toggle `[⊞ Grid] [◉ Map]` chỉ hiện khi ≥ 2 docs
  - Map data lazy-load khi user switch sang map view (1 lần, cache trong state)
  - Delete doc → invalidate mapData (force refresh khi quay lại)
- [x] Build verified: ✓ 2173 modules, 0 errors

**Output artifacts:**
- `frontend/src/features/library/LibrarySimilarityMap.jsx` — file mới
- `frontend/src/features/library/LibraryPage.jsx` — cập nhật với view toggle
- `frontend/src/services/documents.js` — thêm `getSimilarityMap`

---

## Phase 4 — Testing ✅ DONE

**Worker**: Tester (`/as-tester`)

**Tasks:**
- [x] Dựng hạ tầng test backend: `pytest.ini`, `tests/conftest.py` (env + ASGI client + dependency overrides), `requirements-dev.txt`
- [x] Unit tests backend (40): cosine similarity, JWT token, gemini parsing/chunking, schema/config validation
- [x] Integration tests backend (27): auth API, qa + SSE stream, library map, documents CRUD — mock DB + Gemini, không cần Postgres/network
- [x] Dựng hạ tầng test frontend: Vitest + jsdom + Testing Library, `vite.config.js` test block, `src/test/setup.js`, script `npm test`
- [x] Frontend tests (17): `cn` util, `Button` component, `qaService.streamAsk` SSE parser (mock fetch, buffer qua chunk boundary, unicode decode)
- [x] Build verified: backend `67 passed`, frontend `17 passed`, `npm run build` ✓

**🐞 Bug phát hiện (đã báo cáo Backend Worker):**
- **BUG #1 (HIGH)**: `requirements.txt` pin `passlib==1.7.4` nhưng không pin `bcrypt` → clean install lấy `bcrypt==5.0.0` không tương thích → **register/login crash `ValueError` runtime**. Fix: pin `bcrypt==4.0.1` (hoặc nâng passlib). Regression guard: `tests/test_auth_api.py`.
- **NOTE (LOW)**: `get_gemini_key` dùng `Header(...)` required → thiếu hẳn header trả **422** (không phải 400 như `docs/API.md` ghi). Whitespace-only mới trả 400. Cần đồng bộ doc hoặc đổi sang `Header(None)` + check.

**Output artifacts:**
- `backend/tests/` — 8 test file + conftest + README
- `backend/pytest.ini`, `backend/requirements-dev.txt`
- `frontend/src/**/*.test.{js,jsx}` — 3 test file + `src/test/setup.js`
- `.gitignore` — thêm Python entries (`.venv`, `__pycache__`, `.pytest_cache`)

**Môi trường:** Python 3.14 mặc định thiếu `ensurepip` → venv dùng `python3.13`. Chi tiết: `backend/tests/README.md`.

---

## Phase 4b — Backend Bug Fix ✅ DONE

**Worker**: Backend Worker (`/as-backend`)

**Bugs đã fix:**
- [x] **BUG #1 (HIGH)**: Pin `bcrypt==4.0.1` trong `requirements.txt` — tránh `bcrypt==5.0.0` incompatible với `passlib==1.7.4` gây crash register/login
- [x] **asyncpg bump**: Nâng `asyncpg==0.29.0` → `0.30.0` — 0.29.0 không có wheel cho Python 3.13
- [x] **NOTE (LOW)**: Đổi `get_gemini_key` từ `Header(...)` → `Header(None)` + manual check — thiếu header giờ trả 400 thay vì 422, đồng bộ với `docs/API.md`
- [x] Regression: `67 passed` — không có test nào fail

**Output artifacts:**
- `backend/requirements.txt` — thêm `bcrypt==4.0.1`, bump `asyncpg==0.30.0`
- `backend/app/middlewares/auth.py` — `get_gemini_key` consistent 400 cho mọi case thiếu/blank key

---

## Phase 5 — DevOps / Deploy ✅ DONE

**Worker**: DevOps (`/as-devops`)

**Tasks:**
- [x] `backend/Dockerfile` — multi-stage Python 3.13-slim, HEALTHCHECK `/health`
- [x] `frontend/Dockerfile` — multi-stage Node 20 build + nginx:alpine serve
- [x] `frontend/nginx.conf` — SPA routing (`try_files`) + `/api/` reverse proxy tới backend + SSE-safe (`proxy_buffering off`)
- [x] `backend/.dockerignore` + `frontend/.dockerignore` — loại trừ tests/venv/node_modules
- [x] `docker-compose.yml` — full stack: PostgreSQL (pgvector/pgvector:pg16) + backend + frontend; DB healthcheck; migrations init script mount
- [x] `.env.example` (root) — tất cả biến cần thiết, không có giá trị thật
- [x] `.github/workflows/ci.yml` — test-backend (pytest) + test-frontend (vitest + build) trên mọi push/PR
- [x] `.github/workflows/deploy.yml` — build & push images tới GHCR → SSH deploy `docker compose pull && up -d`

**Output artifacts:**
- `backend/Dockerfile`
- `backend/.dockerignore`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `frontend/.dockerignore`
- `docker-compose.yml`
- `.env.example`
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`

**GitHub Secrets cần cấu hình trên repo:**
- `DEPLOY_HOST` — IP hoặc hostname server
- `DEPLOY_USER` — SSH user trên server
- `DEPLOY_SSH_KEY` — private key SSH (server cần public key tương ứng trong `authorized_keys`)
- `GITHUB_TOKEN` — tự động có sẵn, dùng push GHCR

**Hướng dẫn deploy lần đầu (trên server):**
```bash
git clone https://github.com/<user>/fdocs ~/fdocs
cd ~/fdocs
cp .env.example .env
# Điền giá trị thật vào .env
docker compose pull
docker compose up -d
```

---

## Phase 6 — Bug fixes & API Key management (DONE)

**Bug fixes (backend):**
- `.mjs` MIME type trong `frontend/nginx.conf` — fix pdf.js worker bị block (octet-stream → application/javascript)
- Null byte (`\x00`) trong `extracted_text` — strip ở schema validator (PostgreSQL UTF-8 từ chối 0x00)
- Embedding model `text-embedding-004` đã bị Google shut down (14/01/2026) → đổi sang `gemini-embedding-001` + `output_dimensionality=768` (khớp vector(768), tránh HNSW limit 2000)
- Atomicity: embed chạy TRƯỚC mọi DB write; document + chunks persist trong 1 transaction → không còn document mồ côi khi embedding fail
- Lỗi Gemini (429 quota / lỗi khác) dịch thành `GeminiQuotaError`/`GeminiServiceError` → HTTP 429/502 message rõ ràng, không lộ stack trace

**API Key management (frontend):**
- Sidebar: link `/settings/api-key` luôn truy cập được (trước chỉ hiện khi thiếu key), amber khi chưa có key
- `ApiKeySetupPage`: đổi key + xoá key + hiển thị trạng thái key hiện tại (masked)
- CommandPalette: thêm action "Cài đặt Gemini API Key"
- Không cần backend: key thuần client-side (localStorage + header `X-Gemini-Key`, stateless)
- **Quota view**: đã cân nhắc và BỎ — Google không expose quota còn lại qua API key thường, client không query được realtime

---

## Research — Gemini API Strategy & Risk Audit ✅ DONE

**Worker**: Research Worker (`/as-researcher`)

**Output artifact:**
- `docs/RESEARCH_api_strategy.md` — audit đầy đủ (đã xác minh đối kháng từng tuyên bố định lượng)

**Phát hiện gốc rễ chính (chưa fix — chờ Backend Worker):**
- `chunk_size=512` là **512 KÝ TỰ** (không phải token) → doc ~8.000 từ sinh ~106–175 chunk
- **`generate_summary` là gốc 429**: gọi `N+1` (~150) `generate_content_async` **tuần tự, không throttle/backoff** → vỡ generation RPM (~5–15) + nguy cơ 504 (~2–4 phút)
- Ingestion (`embed_texts`) sống sót RPM nhờ throttle nhưng **forced-sleep 100–170s** cho doc dài → nguy cơ 504 (đã có item async-job/SSE trong TODO.md)
- Ánh xạ quota không nhất quán: chỉ embed map `GeminiQuotaError`; `generate_knowledge_graph` nuốt lỗi quota → **500 thay vì 429** + retry 3× không backoff
- JSON parse trần ở keywords/relevance/time-plan → **500 mờ**; stream Q&A lỗi giữa chừng → 200 cụt + lưu answer dở

**Khuyến nghị (3 giai đoạn):** GĐ1 backoff+jitter (#2) + `Retry-After` (#1) + sửa summary/KG/JSON guard → GĐ2 async job + SSE (BackgroundTasks, chưa Redis) → GĐ3 token-bucket per-key (#4). Để embedding cache (#6) sau cùng.

**Action Items**: xem cuối `docs/RESEARCH_api_strategy.md` (gắn tag `[Backend Worker]` / `[Frontend Worker]` / `[DB Worker]` / `[DevOps Worker]`).

---

## Phase 7 — Backend Rate-Limit Hardening (P0 / Giai đoạn 1) ✅ DONE

**Worker**: Backend Worker (`/as-backend`)

**Input**: `docs/RESEARCH_api_strategy.md` — Action Items P0.

**Tasks:**
- [x] **Choke point `_call_with_backoff`**: 1 wrapper retry exponential backoff + jitter cho MỌI call Gemini (embed + generation). Persistent 429 → `GeminiQuotaError` (429); non-quota → `GeminiServiceError` (502). Đọc `Retry-After`/`retry_delay` làm cận dưới; bỏ retry nếu server đòi chờ > 12s. `max_retries=2` cho Q&A (NFR <10s).
- [x] **Viết lại `generate_summary`** (gốc 429 chính): từ `~N+1` call/512-char-chunk → **map-reduce trên segment ~12k ký tự** → còn vài call. Regression test khoá `< 15` call cho doc ~56k ký tự (cũ ~100+).
- [x] **Fix `generate_knowledge_graph`**: chỉ `except json.JSONDecodeError` (quota KHÔNG còn bị nuốt → 429 đúng); bỏ `return {}` dead code; validate `nodes`/`edges`.
- [x] **Guard JSON + `response.text`**: keywords/relevance/time-plan bọc `json.loads` + validate type; `_extract_text` bắt `ValueError` (candidate bị safety-block) → 502 thay vì 500 mờ.
- [x] **Harden `_is_quota_error`**: walk `__cause__` chain (langchain bọc `ResourceExhausted` trong `GoogleGenerativeAIError`).
- [x] **Stream Q&A** (`qa_service`): phát error frame in-band (`{"error","detail"}`) khi lỗi; **chỉ lưu `qa_history` khi stream hoàn tất** (không lưu answer dở); persist bọc try/except log.
- [x] **Review đối kháng (3 lens read-only)** → xử lý 2 regression NFR-timing (medium): (1) `embed_query` dùng `max_retries=2` cho Q&A path (trước dùng default 3 → tổng embed+answer có thể vượt NFR <10s); (2) cap `SUMMARY_MAX_SEGMENTS=12` cho summary (map tuần tự + delay có thể vượt NFR <60s với doc rất dài). Cleanup: clamp 1 lần sleep ≤ ceiling; KG structural-invalid fail ngay (không retry-burst); payload cap `MAX_EXTRACTED_TEXT_CHARS=1M` (security.md).
- [x] Test: **104 passed** (+20 regression test: backoff, retry budget embed_query=2/embed_texts=3, summary call-count + segment cap, KG quota-not-swallowed, JSON validation, extract_text guard, is_quota_error cause-chain, SSE error-frame).
- [x] `docs/API.md`: thêm 429/502 + format SSE error frame.

---

## Phase 8 — Frontend Error Handling (P1 sau backend P0) ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Input**: action item `[Frontend Worker]` từ `docs/RESEARCH_api_strategy.md` + thay đổi backend Phase 7 (`docs/API.md`).

**Tasks:**
- [x] `services/qa.js` — `streamAsk` thêm callback `onError`: bắt cả (a) response không OK ban đầu (429/502 từ embed_query/auth, đọc `detail` từ JSON body) và (b) **in-band SSE error frame** `{"error","detail"}` giữa stream → phân biệt với token (object có key `error` vs token là JSON string). `[DONE]`/error là terminal.
- [x] `understand-mode/QAPanel.jsx` — nối `onError` → banner lỗi (`var(--error)`/`var(--error-bg)`); reload history khi xong (drop optimistic question nếu stream lỗi, đồng bộ với backend "không lưu answer dở"); clear lỗi khi hỏi mới.
- [x] `understand-mode/KnowledgeGraphPanel.jsx` — `catch {}` trống → surface `err.response.data.detail` (KG giờ phân biệt 429/502).
- [x] `upload/UploadPage.jsx` — cảnh báo client-side khi `extracted_text` > `MAX_EXTRACTED_TEXT_CHARS` (1M, mirror backend) trước khi upload; đồng bộ màu lỗi/success sang `var(--error)`/`var(--success)`.
- [x] Các panel Summary/Keywords/Relevance/TimePlan: **không đổi** — đã hiển thị sẵn `err.response.data.detail` → tự nhận message 429/502 mới.
- [x] Test: **frontend 24 passed** (qa.test.js 7→10: error frame, terminal-on-error, non-ok detail); `npm run build` ✓.

**Output artifacts:**
- `frontend/src/services/qa.js`, `frontend/src/services/qa.test.js`
- `frontend/src/features/document/understand-mode/QAPanel.jsx`, `KnowledgeGraphPanel.jsx`
- `frontend/src/features/upload/UploadPage.jsx`

**Còn lại (P1 backend):** ~~async job + SSE *progress* upload~~ → **đã làm ở Phase 9**.

**Chưa làm (chuyển giai đoạn sau / worker khác):**
- P1 `[Backend]`: async job + SSE progress upload (né 504 cho doc dài) — đã có item trong `TODO.md`.
- P1 `[Frontend]`: xử lý error frame SSE + thông điệp 429/502 trên UI.
- Cảnh báo (không fix trong P0): `_make_client` dùng `genai.configure` global → nguy cơ race key giữa request đồng thời (BYOK). Cần quyết định kiến trúc riêng (đổi sang client per-call / SDK mới) — escalate, không tự đổi.

**Output artifacts:**
- `backend/app/services/gemini_service.py` — rewrite: backoff choke point, map-reduce summary, KG fix, JSON/text guards
- `backend/app/services/qa_service.py` — stream error frame + save-on-complete
- `backend/tests/test_gemini_service.py` — +regression tests
- `docs/API.md` — error responses 429/502 + SSE error frame

---

## Phase 9 — Async Upload + SSE Progress (P1) ✅ DONE

**Worker**: Backend Worker (`/as-backend`) → Frontend Worker (`/as-frontend`)

**Input**: item `SSE Progress cho Upload` trong `TODO.md`; mục "Còn lại" Phase 8.

**Vấn đề**: `POST /api/documents` chạy chunk→embed→save **đồng bộ** trong HTTP request (100–170s với doc dài) → nguy cơ 504. FE chỉ có estimate-timer (đếm ngược ước lượng, không phải tiến trình thật).

**Quyết định kiến trúc:**
- SSE dùng **fetch-based** (không `EventSource`) để gửi JWT qua header `Authorization` — nhất quán với `qa/stream`, không lộ token qua query param. *(chốt với người dùng)*
- Handle = `job_id` (không phải `doc_id`) → **không đổi schema DB**; document vẫn chỉ tạo sau khi embed xong (giữ invariant "không doc mồ côi"); `doc_id` trả trong event `done`.
- Job store **in-memory per-process**; Gemini key BYOK chỉ giữ trong RAM, không persist. Hạn chế: **single-worker** (ghi rõ trong `docs/API.md`).

**Tasks (Backend):**
- [x] `gemini_service.embed_texts` — thêm `progress_callback(done, total)` gọi sau mỗi batch.
- [x] `document_service.create_document` — nhận `progress_cb(step, percent)`; mốc chunking=5 / embedding 5–90 (map từ batch) / saving=95.
- [x] `services/upload_job_service.py` (mới) — registry in-memory, `enqueue` (`asyncio.create_task` + session DB riêng), pipeline `_run`, SSE `build_progress_response` (push-based qua `asyncio.Queue`, keepalive 15s, TTL 300s, replay terminal khi reconnect).
- [x] `routes/documents.py` — `POST` → **202** + `DocumentJobResponse{job_id}`.
- [x] `routes/upload.py` (mới) — `GET /api/upload/{job_id}/progress` (auth JWT, chỉ chủ sở hữu, khác user → 404).
- [x] Test: **113 passed** (test_documents 201→202 + 2 test transaction chuyển xuống tầng service; +9 `test_upload_job.py`: progress→done+doc_id, map lỗi quota/service/server, phân quyền 404, SSE stream + replay).

**Tasks (Frontend):**
- [x] `services/documents.js` — `create` trả `{job_id}`; thêm `streamProgress(jobId, {onProgress, onDone, onError})` (fetch-based SSE, bỏ qua keepalive, báo lỗi khi stream đóng sớm).
- [x] `features/upload/UploadPage.jsx` — bỏ estimate-timer; progress bar + `%` realtime từ SSE; `onDone` → điều hướng `/document/{doc_id}`; `onError` → hiện lỗi, về `idle`; cleanup cancel khi unmount.
- [x] Test: **frontend 32 passed** (+`documents.test.js` 8 test: progress→done, ghép frame qua chunk, error frame không gọi onDone, bỏ keepalive, non-ok detail, đóng sớm, header/cancel); `npm run build` ✓.

**Output artifacts:**
- `backend/app/services/upload_job_service.py`, `backend/app/routes/upload.py` (mới)
- `backend/app/services/gemini_service.py`, `document_service.py`, `schemas/document.py`, `routes/documents.py`, `app/main.py`
- `backend/tests/test_upload_job.py` (mới), `backend/tests/test_documents_api.py`
- `frontend/src/services/documents.js`, `frontend/src/features/upload/UploadPage.jsx`, `frontend/src/services/documents.test.js`
- `docs/API.md` (POST 202 + endpoint progress SSE), `TODO.md` (đánh dấu xong)

**Còn lại:**
- Multi-worker: job store cần shared bus (Redis pub/sub) — hiện single-worker.
- Cảnh báo (chưa fix): `genai.configure` global race key BYOK (escalate, chờ quyết định kiến trúc).

---

## Phase 10 — UI Rendering Improvements ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Input**: Approved spec từ PM (2026-06-17). Screenshot app tại `play3cr.dpdns.org` cho thấy 2 vấn đề UX.

**Tasks:**

### Feature 1 — Markdown Rendering cho LLM Output
- [x] Cài `react-markdown` + `remark-gfm`
- [x] `SummaryPanel.jsx` — bọc summary text bằng `<ReactMarkdown>`
- [x] `QAPanel.jsx` — render markdown cho answer của từng Q&A item
- [x] `RelevancePanel.jsx` — render explanation text
- [x] `TimePlanPanel.jsx` — render nếu có markdown

### Feature 2 — PDF Viewer (pdf.js canvas)
- [x] `utils/pdf-store.js` (mới) — IndexedDB helpers: `savePdf(docId, arrayBuffer)`, `loadPdf(docId)`, `deletePdf(docId)`
- [x] `UploadPage.jsx` — sau khi nhận `doc_id` từ SSE `done` event, gọi `savePdf(doc_id, arrayBuffer)` (giữ file trong memory từ lúc parse)
- [x] `components/PdfViewer.jsx` (mới) — load từ IndexedDB, render từng trang qua pdf.js canvas, scroll infinite, fallback graceful nếu không tìm thấy
- [x] `DocumentPage.jsx` — thay "NỘI DUNG VĂN BẢN" text dump bằng `<PdfViewer docId={doc.id} fileType={doc.file_type} fallbackText={doc.extracted_text} />`

**Output artifacts:**
- `frontend/src/utils/pdf-store.js` (mới)
- `frontend/src/components/PdfViewer.jsx` (mới)
- `frontend/src/features/document/DocumentPage.jsx`
- `frontend/src/features/upload/UploadPage.jsx`
- `frontend/src/features/document/read-mode/SummaryPanel.jsx`, `RelevancePanel.jsx`, `TimePlanPanel.jsx`
- `frontend/src/features/document/understand-mode/QAPanel.jsx`

---

## Phase 11 — Prompt Engineering Implementation ✅ DONE

**Worker**: Backend Worker (`/as-backend`)

**Input**: `docs/PROMPT_ENG_spec.md` — complete spec với exact text sẵn sàng để implement.

**Context**: Research Worker + Prompt Engineering Worker đã hoàn thành 2 giai đoạn research:
- Per-Feature system instructions (Option B) được chọn — xem `docs/RESEARCH_system_prompt_design.md`
- Exact prompt text cho tất cả 7 user-turn prompts + 2 system instructions — xem `docs/PROMPT_ENG_spec.md`

**Vấn đề cần giải quyết:**
- LLM output tiếng Anh cho tài liệu tiếng Việt (không có `system_instruction` nào trên model instances)
- LLM thêm filler phrases ("Tất nhiên!", "Dưới đây là...") vì không có anti-filler rule
- Hallucination trong Q&A ("có thể", "dựa trên logic suy ra") vì "say so" quá mơ hồ
- KG node labels tiếng Anh, edge labels là noun phrase thay vì verb
- Summary là plain text, không có structure dù Phase 10 đã render Markdown

**Tasks (theo thứ tự — không đảo):**

### P0 — System Instructions + Factory Functions (Risk: Thấp)
- [x] Thêm `_SYSTEM_TEXT` constant vào `gemini_service.py` (exact text tại Phần 1.1 của spec)
- [x] Thêm `_SYSTEM_JSON` constant vào `gemini_service.py` (exact text tại Phần 1.2 của spec)
- [x] `_make_client(api_key, system_instruction=_SYSTEM_TEXT)` — thêm optional param
- [x] `_make_json_client(api_key, schema, system_instruction=_SYSTEM_JSON)` — thêm optional param
- [x] `extract_keywords`, `score_relevance`, `generate_time_plan` → `_make_client(..., system_instruction=_SYSTEM_JSON)`
- [x] Run `pytest backend/` — **113 passed**

### P1 — Summary + KG + Keywords Prompts (Risk: Thấp)
- [x] `generate_summary` map step: Vietnamese prompt + ### heading + bullet list instruction
- [x] `generate_summary` reduce step: Vietnamese prompt + ## heading + dedup + logical ordering
- [x] `generate_knowledge_graph`: max 20 nodes + quality criteria + verb-phrase edge rule
- [x] `extract_keywords`: Vietnamese prompt + 3-tier priority criteria
- [x] Run `pytest backend/` — **113 passed**

### P2a — Relevance Prompt (Risk: Trung bình)
- [x] `score_relevance`: Vietnamese prompt + 5-range rubric + 3-sentence explanation with **bold**
- [x] Run `pytest backend/` — **113 passed**

### P2b — Q&A Prompt (Risk: Trung bình)
- [x] Extract `_qa_prompt()` shared helper — dùng cho cả `answer_question` + `answer_question_stream`
- [x] Vietnamese prompt + language-override ("Trả lời bằng cùng ngôn ngữ với câu hỏi")
- [x] Specific fallback phrase + explicit ban hedging language
- [x] Run `pytest backend/` — **113 passed**

**Output artifacts:**
- `backend/app/services/gemini_service.py` — 4 commits: P0 (system instructions + factory), P1 (summary/kg/keywords), P2a (relevance), P2b (Q&A)
- `backend/tests/test_gemini_service.py` — cập nhật lambda mocks để nhận `**kw`

**Test thủ công cần verify sau khi deploy:**
1. Upload tài liệu tiếng Việt → Summary có heading/bullet, tiếng Việt
2. Upload tài liệu tiếng Anh → Summary tiếng Anh
3. Q&A: hỏi tiếng Việt trên tài liệu tiếng Anh → reply tiếng Việt
4. Q&A: hỏi ngoài tài liệu → chỉ "Tài liệu không đề cập đến điều này."
5. KG: node labels đúng ngôn ngữ, edge labels là verb phrase, ≤ 20 nodes

---

## Phase 3e — Knowledge Graph UI Enhancement ✅ DONE

**Workers**: Designer Worker (`/as-designer`) → Frontend Worker (`/as-frontend`)

**Tasks:**
- [x] Design spec đầy đủ: `docs/KG_DESIGN_SPEC.md` — hover tooltip, click highlight, legend, table fallback
- [x] Edge label improvements: font-size 9→10, text-background pill, opacity 0.7 baseline
- [x] Legend: DOM element absolute bottom-right, 3 rows (concept/entity/process), ẩn mobile
- [x] Hover tooltip: DOM-based, delay 120ms, flip logic rìa canvas, ẩn trên touch device
- [x] Click highlight: ego network (dimmed/highlighted/selected classes), deselect click 2 lần, reset click empty
- [x] Double-click node: fit neighborhood (animated 400ms)
- [x] Fit button: reset highlight trước khi fit
- [x] OQ-2: ẩn edge labels khi > 25 edges + "Hide/Show labels" toggle
- [x] Accessibility table fallback: `KGTable.jsx` riêng, 2 tabs Nodes/Edges, sticky header, ARIA đầy đủ
- [x] Error color: đổi `text-red-500` → `text-[var(--error)]`
- [x] Build verified: ✓

**Output artifacts:**
- `frontend/src/features/document/understand-mode/KnowledgeGraphPanel.jsx` — enhanced
- `frontend/src/features/document/understand-mode/KGTable.jsx` — file mới
- `docs/KG_DESIGN_SPEC.md` — design spec

---

## Phase 3e.1 — Knowledge Graph Visual Fixes ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Input**: Feedback trực tiếp từ screenshot người dùng (play3cr.dpdns.org).

**Tasks:**
- [x] Node auto-size: `width/height: 'label'` + `padding: '10px 14px'` + `text-max-width: 130` + `font-size: 12`
- [x] Layout params: `nodeRepulsion 8000→450000`, `idealEdgeLength 100→160`, `gravity 0.25`, `numIter 1500`, extract `COSE_LAYOUT` constant
- [x] Nút "Rearrange": re-run COSE layout không destroy graph, chỉ hiện khi có graph
- [x] Edge label contrast: thêm `edgeLabel` color vào `THEME_COLORS` (neutral: #64748B, cream: #7C6E5C, dark: #A1A1AA), `text-background-opacity 0.85→0.92`
- [x] Build verified: ✓

**Output artifacts:**
- `frontend/src/features/document/understand-mode/KnowledgeGraphPanel.jsx`

---

## Phase 16 — Prompt Engineering Update: Grounding + LaTeX ✅ DONE

**Worker**: Prompt Engineering Worker

**Issues addressed:**
1. **Q&A grounding quá strict**: Câu hỏi tổng quan ("Chapter này nói về gì?") bị trả "Tài liệu không đề cập" dù chunks chứa đủ nội dung.
2. **LaTeX**: Frontend đã render KaTeX (Phase 13) nhưng LLM chưa biết → không dùng LaTeX.

**Root cause grounding bug**: Rule "Nếu câu trả lời KHÔNG có trong ngữ cảnh" bị model áp dụng quá literal — câu hỏi tổng quan cần synthesis, không phải lookup câu explicit.

**Tasks:**
- [x] `_SYSTEM_TEXT`: Sửa GROUNDING — thêm "Tổng hợp và suy luận từ nội dung được cung cấp là hợp lệ"
- [x] `_SYSTEM_TEXT`: Thêm ĐỊNH DẠNG LaTeX — `$...$` inline, `$$...$$` display, mention KaTeX
- [x] `_qa_prompt`: Relaxed grounding rule — "có thể rút ra (trực tiếp hoặc tổng hợp)"
- [x] `_qa_prompt`: Explicit carve-out cho overview questions ("nói về gì?", "chủ đề là gì?")
- [x] `_qa_prompt`: Làm rõ fallback — "THỰC SỰ VẮNG MẶT trong toàn bộ ngữ cảnh"
- [x] `docs/PROMPT_ENG_spec.md`: Cập nhật 2.7 + thêm mục 2.8

**Output artifacts:**
- `backend/app/services/gemini_service.py` — `_SYSTEM_TEXT`, `_qa_prompt` updated
- `docs/PROMPT_ENG_spec.md` — Section 2.7 revised, Section 2.8 added

---

## Phase 15b — Hotfix: React error #310 ✅ DONE

**Bug**: React error #310 "Rendered more hooks than during previous render" sau Phase 15.

**Root cause**: `useEffect` ở dòng 32 của `AppLayout.jsx` nằm SAU `if (isLoading) return null` (dòng 22). Khi `isLoading=true` React gọi 6 hooks; khi `false` gọi 7 hooks → vi phạm Rules of Hooks.

**Fix**: Di chuyển `toggleCollapsed` + `useEffect` lên trước cả hai early returns — tất cả hooks phải được gọi trước bất kỳ conditional return nào.

**Output:** `frontend/src/layouts/AppLayout.jsx` — build ✓ 2.39s

---

## Phase 15 — Session Persistence Fix ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Bug**: Refresh trang → user bị logout vì `accessToken` lưu trong React state (reset về `null` khi reload). Refresh token httpOnly cookie vẫn còn nhưng không được dùng.

**Root cause**: `AuthContext` không gọi `authService.refresh()` khi mount. `AppLayout` redirect `/login` ngay khi `!isAuthenticated` mà không chờ refresh attempt.

**Fix:**
- [x] `AuthContext.jsx` — thêm `isLoading = true` state + `useEffect` gọi `authService.refresh()` on mount; set `isLoading = false` trong `.finally()`; expose `isLoading` qua context
- [x] `AppLayout.jsx` — thêm guard `if (isLoading) return null` trước `if (!isAuthenticated)` redirect
- [x] Build verified: ✓ 2.07s

**Output artifacts:**
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/layouts/AppLayout.jsx`

---

## Phase 14 — Q&A UX Improvements ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Tasks:**
- [x] Nút "Xóa lịch sử" (Trash2 icon, ghost/sm): hiện khi có history + không đang streaming, xóa local state
- [x] Auto-scroll fix: wrap `scrollIntoView` trong `setTimeout(50ms)` với cleanup để tránh race condition DOM
- [x] Message order verified: oldest-first (chronological) = tự nhiên như chat, không cần thay đổi
- [x] Empty state cải thiện: 2 dòng centered thay vì 1 dòng text đơn
- [x] Build verified: ✓ 2.03s

**Output artifacts:**
- `frontend/src/features/document/understand-mode/QAPanel.jsx`

---

## Phase 13 — LaTeX + Markdown Rendering ✅ DONE

**Worker**: Frontend Worker (`/as-frontend`)

**Tasks:**
- [x] Install `remark-math`, `rehype-katex`, `katex`
- [x] `main.jsx` — import `katex/dist/katex.min.css`
- [x] `components/ui/MarkdownLatex.jsx` — shared component wrap ReactMarkdown + remarkGfm + remarkMath + rehypeKatex
- [x] `SummaryPanel.jsx` — dùng `MarkdownLatex` thay ReactMarkdown
- [x] `RelevancePanel.jsx` — dùng `MarkdownLatex`
- [x] `QAPanel.jsx` — dùng `MarkdownLatex` cho cả history answers và streaming text
- [x] Build verified: ✓ 2457 modules

**Output artifacts:**
- `frontend/src/components/ui/MarkdownLatex.jsx` — file mới
- `frontend/src/main.jsx`, `SummaryPanel.jsx`, `RelevancePanel.jsx`, `QAPanel.jsx`

---

## Phase 12 — Settings Page 🚧 IN PROGRESS

**Workers**: Frontend Worker (`/as-frontend`) → Backend Worker (`/as-backend`)

**Mục tiêu**: Trang `/settings` tập trung cho phép user cấu hình language preference của AI responses + quản lý API key.

**Quyết định kiến trúc:**
- Storage: `localStorage` — không cần backend endpoint mới cho settings
- Language preference: `fdocs:lang` (`auto | vi | en`)
- Backend nhận preference qua header `X-Response-Language` (optional)
- Frontend Worker làm trước — không block backend

### Frontend Tasks
- [ ] `LanguagePrefContext` — expose `lang` (`auto|vi|en`) + `setLang`, persist `localStorage` key `fdocs:lang`
- [ ] `/settings` page với 2 section:
  - "Ngôn ngữ AI": 3 radio options — Auto / Tiếng Việt / English (kèm mô tả ngắn mỗi option)
  - "Gemini API Key": inline content của `ApiKeySetupPage` (copy UI, không redirect)
- [ ] Route `/settings` trong `main.jsx`
- [ ] Sidebar: đổi link từ `/settings/api-key` → `/settings`
- [ ] Mọi API call trong `services/` thêm header `X-Response-Language: vi|en` khi `lang !== 'auto'` (bỏ qua khi auto)
- [ ] `npm run build` ✓

### Backend Tasks
- [ ] Header dependency `get_response_language` (optional, default `None`) — đọc `X-Response-Language`
- [ ] Inject language directive vào user-turn prompt khi override được set:
  - `vi` → append `"\nHãy trả lời bằng tiếng Việt."` vào cuối prompt
  - `en` → append `"\nPlease respond in English."` vào cuối prompt
- [ ] Áp dụng cho: `generate_summary` (map + reduce), `score_relevance` (explanation), `answer_question`, `answer_question_stream`
- [ ] **Không** áp dụng cho: `extract_keywords`, `generate_knowledge_graph` (labels là ngôn ngữ tài liệu)
- [ ] `pytest backend/` — số lượng passed không giảm

---

## Phase: Q&A False-Positive Reduction (RAG) — 2026-06-18

**Vấn đề:** Q&A trả "Tài liệu không đề cập" cho câu hỏi thực ra CÓ liên quan (false-positive), do retrieval recall thấp + prompt 2-trạng-thái quá cứng. Ràng buộc bất biến: không được tăng hallucination/lan man.

**Đầu ra nghiên cứu:** `docs/RESEARCH_qa_false_positive.md` — root cause: chủ yếu RETRIEVAL (top_k=5 semantic thuần, không hybrid/re-rank), prompt khuếch đại. Loại trừ embedding 768-dim.

### Đã hoàn thành (live trên app)
- [x] **Backend GĐ1** — `qa_service.py`: top_k 5→12 (`QA_TOP_K`), candidate pool `QA_FETCH_K=30`.
- [x] **Backend GĐ2** — Hybrid retrieval: semantic (cosine) + lexical (`get_similar_lexical`, Postgres full-text 'simple') fuse bằng **RRF** (`_rrf_fuse`, `RRF_K=60`) → top 12. (MMR của GĐ1 bị thay vì xung đột với hybrid.) Lexical on-the-fly, không migration. Unit test `test_rrf_fuse_dedups_and_ranks`.
- [x] **Prompt Eng spec** — `docs/PROMPT_qa_versions.md`: 3 bản strict/balanced/permissive, logic 3-trạng-thái (trả lời / liên quan một phần / từ chối), giữ baseline chống hallucination.
- [x] **Backend áp prompt BALANCED** — `_qa_prompt` + dòng GROUNDING (`_SYSTEM_TEXT`). Đổi đúng 2 chỗ.

### Còn lại
- [x] **Validation: UAT người thật** (2026-06-18) — phản hồi định tính: tốt hơn rõ rệt so với bản cũ, không phát hiện hallucination. Chốt **balanced** làm mặc định.
- [ ] (Tùy chọn về sau) đòn bẩy tinh chỉnh nếu cần: prompt strict (nếu xuất hiện hallucination) / permissive (nếu còn từ chối sai) — chỉ đổi text `_qa_prompt`, rollback tức thì.
- [ ] (GĐ3 — chỉ nếu UAT chưa đạt) re-rank cross-encoder / HyDE.

**Files chạm:** `backend/app/services/qa_service.py`, `backend/app/repositories/chunk_repository.py`, `backend/app/services/gemini_service.py`, `backend/tests/test_qa_api.py`, `docs/RESEARCH_qa_false_positive.md`, `docs/PROMPT_qa_versions.md`.
