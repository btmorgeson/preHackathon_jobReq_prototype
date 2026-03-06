# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend

```bash
# Run tests
PYTHONPATH=. pytest -q

# Run a single test file
PYTHONPATH=. pytest tests/test_hybrid_retriever.py -v

# Start API server (uvicorn not on PATH — always use python -m)
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000

# Run smoke tests (requires live server + Neo4j VM)
PYTHONPATH=. python scripts/06_smoke_test.py
```

### Frontend (run from `frontend/`)

```bash
npm.cmd run dev         # dev server → http://localhost:3000
npm.cmd run build       # production build (CI gate)
npm.cmd run lint        # ESLint
npm.cmd run test:e2e    # Playwright e2e (3 mocked-flow specs)
```

### Data pipeline (in order)

```bash
PYTHONPATH=. python scripts/01_fetch_onet.py
PYTHONPATH=. python scripts/02_generate_employees.py
PYTHONPATH=. python scripts/03_build_graph_csv.py
vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"
PYTHONPATH=. python scripts/05_embed_chunks.py    # requires GENESIS_SKLZ_API_KEY
```

### Task runner shorthand (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task api
powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task pipeline
powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task smoke
```

---

## Architecture

### Data flow

```
O*NET fetch → synthetic employees (Faker) → graph CSVs
    → Neo4j import (Vagrant VM, neo4j-admin bulk import)
    → embeddings + vector indexes (Genesis MXBai 1024-dim)
    → FastAPI search API → Next.js frontend
```

### Backend (`src/`)

- **`src/config.py`** — `get_settings()` singleton (`@lru_cache`). Reads all env vars. Always import settings from here, never `os.environ` directly.
- **`src/api/`** — FastAPI app. `main.py` owns lifespan (Neo4j driver), CORS, request-ID middleware, and centralized exception handlers. Routers under `routers/`: `search.py` (`POST /api/search`), `postings.py` (`GET /api/postings/{req_number}`), `skills.py` (`POST /api/extract-skills`).
- **`src/graph/hybrid_retriever.py`** — Core retrieval logic. Two-stage Graph RAG:
  1. Graph seed: path traversal `Posting → REQUIRES_SKILL → Skill ← HAS_SKILL ← Person`
  2. Filtered vector re-rank: chunk + role vector search scoped to seeded candidate IDs
  3. Batched LLM evidence: single Claude call with `CANDIDATE N:` plain-text markers
- **`src/graph/queries.py`** — All Cypher constants. Never inline Cypher in retriever logic.
- **`src/scoring/aggregator.py`** — Delegates to `HybridRetriever`. Exposes 3-pillar composite: skill match, role history, experience chunk similarity.
- **`src/pipeline/`** — One-time pipeline scripts. `embed/embed_pipeline.py` runs embeddings and `link_chunk_mentions()` entity linker.

### Frontend (`frontend/`)

Next.js 16 App Router. Four components: `SearchForm`, `CandidateTable` (TanStack Table), `ScoreBreakdown` (Recharts), `SkillEditor`. API base URL centralized in `lib/apiConfig.ts`. No Google Fonts (blocked on corporate network) — system font stacks in `globals.css`.

---

## Critical Constraints

### Environment

- **`PYTHONPATH=.` is required** for all scripts and pytest — no venv, no editable install.
- **`GENESIS_SKLZ_API_KEY`** is not inherited by Git Bash. Export manually:
  ```bash
  export GENESIS_SKLZ_API_KEY="$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('GENESIS_SKLZ_API_KEY','User')" | tr -d '\r')"
  ```
- SSL cert for Python HTTP: `C:/Users/%USERNAME%/combined_pem.pem`. `get_settings()` sets `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` automatically on import.

### LLM / Genesis API

- **Dual-LLM pattern**: `claude-4-5-sonnet-latest` for reasoning, `gpt-oss-120b` for structured JSON extraction.
- **Never use `response_format: {type: "json_schema"}` with Claude** — returns HTTP 500. Claude returns plain text; GPT does structured extraction.
- Genesis base URL: `https://api.ai.us.lmco.com/v1`, org header: `openai-organization: SKLZ`.

### Neo4j / data model

- Vagrant VM: `bolt://localhost:7687`, creds `neo4j`/`password12345`, `http://localhost:7474`.
- In graph CSV import, `:ID` is NOT stored as a node property. `stable_id` must be a separate column.
- Vector index dims: **1024** (must match `mxbai-embed-large-v1`).
- Filtered vector re-rank Cypher: `WHERE p.stable_id IN $candidate_ids` goes AFTER `YIELD` — Neo4j constraint.

### Pydantic v2 serialization

- `exc.errors()` ctx may contain `ValueError` objects — not JSON serializable. Use `_sanitize_validation_errors()` in `src/api/main.py` before passing to `JSONResponse`.

### Frontend

- **Never use `next/font/google`** — Google Fonts are blocked on the corporate network and cause a hard build failure. Use `next/font/local` or system fonts only.
- On Windows, `npm` must be invoked as `npm.cmd` from Git Bash. Same for `npx.cmd`.
- `uvicorn --reload` file watcher does not pick up changes on Windows — restart the server manually after edits.
