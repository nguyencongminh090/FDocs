# FDocs — Progress Tracker

> Cập nhật lần cuối: 2026-06-15

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

## Phase 4 — Testing ⏳ PENDING

**Worker**: Tester (`/as-tester`)  
**Chờ**: Phase 2 + 3 hoàn thành

---

## Phase 5 — DevOps / Deploy ⏳ PENDING

**Worker**: DevOps (`/as-devops`)  
**Chờ**: Phase 4 pass
