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

**Chưa làm (chuyển giai đoạn sau / worker khác):**
- P1 `[Backend]`: async job + SSE progress upload (né 504 cho doc dài) — đã có item trong `TODO.md`.
- P1 `[Frontend]`: xử lý error frame SSE + thông điệp 429/502 trên UI.
- Cảnh báo (không fix trong P0): `_make_client` dùng `genai.configure` global → nguy cơ race key giữa request đồng thời (BYOK). Cần quyết định kiến trúc riêng (đổi sang client per-call / SDK mới) — escalate, không tự đổi.

**Output artifacts:**
- `backend/app/services/gemini_service.py` — rewrite: backoff choke point, map-reduce summary, KG fix, JSON/text guards
- `backend/app/services/qa_service.py` — stream error frame + save-on-complete
- `backend/tests/test_gemini_service.py` — +regression tests
- `docs/API.md` — error responses 429/502 + SSE error frame
