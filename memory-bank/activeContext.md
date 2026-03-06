# Active Context

## Current Task
Frontend UI/UX readability fix (2026-03-06) — COMPLETE.

## Session: Frontend Font & Typography Fix (2026-03-06)
- **Problem**: Font was hard to read. `globals.css` referenced Geist font variables (`--font-geist-sans`, `--font-geist-mono`) that were never imported. Body fell back to `Arial, Helvetica, sans-serif`. Heavy use of `text-xs` (12px) for content text.
- **Root cause**: Default Next.js template references `next/font/google` Geist fonts, but Google Fonts is blocked on corporate network (TLS interception). Previous fix removed the import but left broken CSS variable references.
- **Fix applied** (7 files):
  - `globals.css`: Removed broken Geist theme refs. Set system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`), base `font-size: 16px`, `line-height: 1.5`.
  - `layout.tsx`: Removed `next/font/google` Inter import (fails on corporate network). Uses system fonts via CSS.
  - All components: Bumped `text-xs` → `text-sm`/`text-base` for content text. Increased table cell padding (`px-3 py-2` → `px-4 py-3`). Reduced score decimals from 3 to 2. Added `shadow-sm` + borders to cards. Larger button touch targets (`py-2.5`).
- **Verification**: `npm run build` succeeds, `npm run lint` passes (0 errors, 1 pre-existing warning).
- **Key learning**: `next/font/google` causes hard build failure on corporate network — always use system font stack or `next/font/local` with bundled font files.

## Previous Session Outcome (2026-03-05)
- Fixed critical bug: `stable_id` property missing from Neo4j nodes after CSV import
- Rebuilt CSVs, re-imported into Vagrant Neo4j, re-ran embedding pipeline
- Started FastAPI backend and verified all endpoints
- Smoke tests: 6/7 pass (1 pre-existing failure on empty-payload error envelope)

## Bug Fix: stable_id Missing from Neo4j Nodes
- **Root cause**: `graph_csv_builder.py` used `row["stable_id"]` as the `:ID` column value but never included `stable_id` as a separate property column. Neo4j's `admin import` treats `:ID` as an internal reference — it doesn't create a visible property.
- **Impact**: Embed pipeline's `MATCH (c:Chunk {stable_id: $id})` silently matched nothing. Embeddings were computed (1498 chunks, 1267 roles) but the `SET` never fired — all writes were no-ops.
- **Fix**: Added `stable_id` as an explicit property column in all 5 node CSVs (persons, roles, skills, chunks, postings) in `src/pipeline/load/graph_csv_builder.py`.
- **Verification**: After rebuild+reimport, nodes have `stable_id` property. Embed pipeline successfully wrote embeddings and created 1148 MENTIONS edges.

## Verified Running State
- Neo4j (Vagrant VM): `http://localhost:7474` / `bolt://localhost:7687` — 3315 nodes, 8558 rels, 14306 properties
- Embeddings: 1498 chunks, 1267 roles embedded; 1148 MENTIONS edges; 2 vector indexes
- FastAPI backend: `http://localhost:8000` — health check OK
- Smoke tests: 6/7 pass
- Search API: `POST /api/search {"req_number":"REQ-001","top_k":3}` returns ranked candidates with scores + evidence

## Operational Flow (Host)
1. `vagrant up`
2. `python scripts/03_build_graph_csv.py` (with `PYTHONPATH=.`)
3. `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"`
4. `PYTHONPATH=. python scripts/05_embed_chunks.py` (requires `GENESIS_SKLZ_API_KEY`)
5. `PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000`
6. `PYTHONPATH=. python scripts/06_smoke_test.py`

## Known Issues
- Smoke test 7/7 fails: empty `{}` payload returns 500 `internal_error` instead of 422 `validation_error`. Model-level validator raises ValueError that isn't caught as RequestValidationError.
- `GENESIS_SKLZ_API_KEY` set via `setx` but not inherited by Git Bash sessions. Must export manually: `export GENESIS_SKLZ_API_KEY="$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('GENESIS_SKLZ_API_KEY','User')" | tr -d '\r')"`
- `uvicorn` not on Git Bash PATH directly — use `python -m uvicorn` instead.
- All scripts need `PYTHONPATH=.` when run from Git Bash (no venv, no editable install).

## Archive
### Previous: Graph RAG Hybrid Retriever code (2026-03-05)
Implemented two-stage Graph RAG replacing global vector seed:
- Created `src/graph/hybrid_retriever.py` — `HybridResult` + `HybridRetriever` class (3 stages)
- Added `link_chunk_mentions()` + `_link_chunk_to_skills()` to `embed_pipeline.py`
- Added 5 new Cypher constants to `queries.py` (`POSTING_GRAPH_SEED`, `SKILL_LIST_GRAPH_SEED`, `CHUNK_VECTOR_FILTERED`, `ROLE_VECTOR_FILTERED`, `PERSON_CHUNK_EVIDENCE`)
- Refactored `aggregator.py` to delegate to `HybridRetriever`; added `posting_req_number` keyword param to `aggregate()`
- Passed `posting_req_number=payload.req_number` in `search.py`
- Added `--rebuild-mentions` flag to `scripts/05_embed_chunks.py`
- Created `tests/test_hybrid_retriever.py` — 7 unit tests, all PASS
- All files compile clean; `_normalize_scores`/`_normalize_weights` preserved for backward compat

### Previous: Vagrant + VirtualBox runtime (2026-03-05)
- Added Vagrantfile, provisioning scripts, import scripts
- VM created with Neo4j 5.26.21, data imported, host connectivity verified

## Session: Frontend Corporate-Tech Refresh + Playwright QA (2026-03-06)
- **Goal**: Upgrade UI from basic gray prototype styling to a modern corporate tech interface while preserving backend contracts.
- **Scope completed**:
  - Reworked global theme (`frontend/app/globals.css`) with tokenized palette, layered light-tech background, panel utility classes, and motion/focus defaults.
  - Upgraded layout shell + status surfaces in `frontend/app/page.tsx`.
  - Refreshed component styling and interaction polish in:
    - `frontend/components/SearchForm.tsx`
    - `frontend/components/SkillEditor.tsx`
    - `frontend/components/CandidateTable.tsx`
    - `frontend/components/ScoreBreakdown.tsx`
  - Updated typography strategy to local corporate font stacks in CSS (no external font fetch dependency).
- **Functional reliability fix**:
  - Search submission now blocks while req lookup/skill extraction is in progress (`Wait for skill sync...`), preventing stale query submissions.
  - Search request summary now uses a stable request snapshot at submit time.
- **Playwright validation loop**:
  - Desktop baseline, req-number flow, role-description flow, row expansion, sort behavior, and score panel checks passed.
  - Mobile viewport validation at `390x844` passed with horizontally scrollable result table.
- **Build/test signal**:
  - `npm.cmd run build` succeeded.
  - `npm.cmd run lint` passed with one existing TanStack React Compiler compatibility warning (no errors).
