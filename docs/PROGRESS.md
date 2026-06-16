# FDocs — Progress Tracker

> Cập nhật lần cuối: 2026-06-16

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
