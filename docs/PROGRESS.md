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

## Phase 1 — Database Schema 🔄 IN PROGRESS

**Worker**: Database Worker (`/as-db`)

**Input**: PRD.md v1.3 — đặc biệt các bảng: `users`, `documents`, `chunks`, `analysis_results`, `qa_history`

**Tasks:**
- [ ] Thiết kế ERD đầy đủ
- [ ] Viết SQL migration files (Alembic hoặc plain SQL)
- [ ] Enable pgvector extension
- [ ] Định nghĩa indexes (pgvector HNSW/IVFFlat cho `chunks.embedding`)

**Output cần có:**
- `docs/schema.md` — ERD dạng text/Mermaid
- `backend/migrations/` — migration files

---

## Phase 2 — Backend API ⏳ PENDING

**Worker**: Backend Worker (`/as-backend`)  
**Chờ**: Phase 1 hoàn thành

---

## Phase 3 — Frontend ⏳ PENDING

**Worker**: Frontend Worker (`/as-frontend`)  
**Chờ**: Phase 2 hoàn thành (API contracts)

---

## Phase 4 — Testing ⏳ PENDING

**Worker**: Tester (`/as-tester`)  
**Chờ**: Phase 2 + 3 hoàn thành

---

## Phase 5 — DevOps / Deploy ⏳ PENDING

**Worker**: DevOps (`/as-devops`)  
**Chờ**: Phase 4 pass
