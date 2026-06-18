# FDocs

> AI-powered reading assistant that helps students read, understand, and retain knowledge from long academic documents — powered by Retrieval-Augmented Generation (RAG) and the Google Gemini API.

🇬🇧 English (default) · 🇻🇳 [Tiếng Việt](README_vi.md)

---

## 📖 What is FDocs?

FDocs turns a dense PDF/DOCX (textbooks, papers, lecture notes) into something a student can actually work through. You upload a document, bring your own Gemini API key, and FDocs gives you a smart reading layer on top of it: summaries, keyword maps, a relevance check before you commit to reading, a knowledge graph, a reading schedule, and a grounded Q&A chat that answers **only** from the document.

## 💡 The idea

Students drown in long, complex material under tight deadlines. The core insight behind FDocs:

- **Decide before you read** — score how relevant a document is to *your* goal first.
- **Read with structure** — summary, keywords, and a knowledge graph give you the shape of the content before the details.
- **Ask, don't scan** — a RAG chat answers questions grounded in the document, with citations to the source chunks, instead of you hunting through 50 pages.
- **Your key, your data** — BYOK (Bring Your Own Key): the Gemini key lives in your browser and the original file is parsed locally, never uploaded.

## 🌱 Why it matters / contribution

- **Privacy-first**: documents are parsed in-browser (pdf.js + mammoth.js); only extracted text reaches the server, and your API key is never stored or logged server-side.
- **Grounded by design**: the Q&A pipeline uses hybrid retrieval (semantic + lexical) and a prompt that refuses to invent facts outside the document — reducing hallucination while still being useful.
- **Open & educational**: a real, end-to-end RAG application (FastAPI + pgvector + Gemini + React) that others can read, learn from, and extend.

## ✨ Features

| Area | Feature |
|---|---|
| **Upload** | PDF / DOCX parsed **in-browser**; only text is sent to the server; realtime upload progress (SSE) |
| **Read mode** | Hierarchical summary · keyword extraction · relevance score (vs. your goal) · related documents · reading time plan |
| **Understand mode** | Interactive **knowledge graph** · **Q&A chat** (RAG, grounded, streaming) |
| **Q&A quality** | Hybrid retrieval (semantic cosine + lexical full-text, fused with RRF) + 3-state grounded prompt (answer / partial / refuse) |
| **Rendering** | Markdown + LaTeX (KaTeX) in AI output |
| **Account & settings** | JWT auth · language preference (Auto/VI/EN) · BYOK Gemini key management |

## 🧱 Tech stack

- **Frontend**: React 19, Vite, Tailwind CSS, React Router, Cytoscape (graph), KaTeX, pdf.js, mammoth.js
- **Backend**: FastAPI, SQLAlchemy (async), LangChain, `google-generativeai`
- **Database**: PostgreSQL + **pgvector** (`gemini-embedding-001`, 768-dim)
- **AI**: Google Gemini (`gemini-2.5-flash` generation + `gemini-embedding-001`)
- **Infra**: Docker Compose, GitHub Actions (CI), Nginx (frontend serving)

---

## 🚀 Setup (step by step)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- A **Google Gemini API key** (free tier works) — get one at [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone
```bash
git clone https://github.com/nguyencongminh090/FDocs.git
cd FDocs
```

### 2. Create the `.env` file (project root)
```env
# Postgres
POSTGRES_USER=fdocs
POSTGRES_PASSWORD=change-me

# Backend
DATABASE_URL=postgresql+asyncpg://fdocs:change-me@db:5432/fdocs
SECRET_KEY=replace-with-output-of-`openssl rand -hex 32`
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
ALLOWED_ORIGINS=http://localhost:3000

# Frontend host port
PORT=3000
```
> ⚠️ Use the Postgres **service host `db`** (not `localhost`) in `DATABASE_URL` — that's the Docker network name. Generate a real secret with `openssl rand -hex 32`.

### 3. Build & run
```bash
docker compose up --build -d
```
This starts three containers: `db` (Postgres + pgvector, schema auto-applied from `backend/migrations/`), `backend` (FastAPI), and `frontend` (Nginx).

### 4. First use
1. Open the app (see below), **register** an account.
2. Go to **Settings → Gemini API Key**, paste your key (stored only in your browser).
3. Upload a PDF/DOCX and start reading.

### Local dev (without Docker, optional)
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000

# Frontend
cd frontend && npm install
npm run dev                            # http://localhost:5173
```
> The project standard package manager is **npm** (CI and Docker use `npm ci`). If you change dependencies, commit the updated `package-lock.json`.

---

## 🌐 Launch / access the site

There is no public deployment yet (see TODO). After `docker compose up`:

| Service | URL |
|---|---|
| **Web app** | `http://localhost:3000` (or your `PORT`) |
| Backend API | `http://localhost:8000` |
| API docs (Swagger) | `http://localhost:8000/docs` |

---

## 🗺️ Roadmap / coming soon

- [ ] **Production deployment** — GitHub Actions deploy via SSH (secrets + server `.env`)
- [ ] **Multi-worker scaling** — upload job store is in-memory today (single worker); move to Redis for a shared job bus
- [ ] **Q&A re-ranking (stage 3)** — cross-encoder re-rank / HyDE if hybrid retrieval isn't enough
- [ ] **Automated Q&A eval set** — measure false-positive & faithfulness over time
- [ ] Full-length async summaries for very long documents

## ⚖️ Pros & Cons

**Strengths**
- Privacy-first BYOK; original files never leave the browser.
- Grounded RAG Q&A with hybrid retrieval — strong against hallucination.
- Self-hostable in one `docker compose up`.
- Markdown + LaTeX rendering, good for STEM material.

**Limitations / weaknesses (honest)**
- **Free-tier Gemini quota**: long documents can hit rate limits (HTTP 429) during embedding/summary.
- **Single-worker upload pipeline**: SSE progress relies on an in-memory job store — not safe across multiple backend workers yet.
- **No live demo / public deployment** yet.
- **Q&A not yet quantitatively evaluated** — validated by human UAT, not an automated metric suite.
- Lexical search runs on-the-fly (no full-text index) — fine per document, not tuned for huge corpora.
- Vietnamese full-text uses the `simple` config (no stemming).

---

## 🤝 Contributing

Contributions are welcome — this is a learning-friendly codebase.

1. Fork & branch from `main` (`feat/...` or `fix/...`); **don't commit to `main` directly**.
2. One logical change per commit; messages as `type(scope): summary` (e.g. `feat(qa): ...`).
3. Run tests before opening a PR: `npm test` (frontend) and `pytest` (backend, dev deps).
4. Open a PR to `main` with a short description + test notes.

See `docs/` for the PRD, schema, API, and design decisions.

## 🎯 Our wish

We hope FDocs makes hard material a little less intimidating — and that students spend less time hunting through pages and more time actually understanding. If it helps you read smarter, that's the goal. ⭐ Star the repo, open an issue, or send a PR.

## 📄 License

License: TBD (to be decided by the team).
