# Active Context

## Current Task
Frontend corporate-tech refresh (2026-03-06) — COMPLETE. Build verified.
Backend stabilization — IN PROGRESS (other agent: commit, 422 fix, smoke tests, pytest).

## Session: Frontend Corporate-Tech Refresh + Playwright QA (2026-03-06)
- **Goal**: Upgrade UI from basic prototype styling to modern corporate tech interface.
- **Scope completed**:
  - Tokenized palette + layered background + panel utility classes + motion/focus defaults in `globals.css`.
  - Hero/status panel, improved summary, stronger state surfaces in `page.tsx`.
  - Refreshed all 4 components: SearchForm, SkillEditor, CandidateTable, ScoreBreakdown.
  - Typography: local corporate font stacks (Segoe UI Variable Text, Bahnschrift for headings) — no external font fetch.
  - `layout.tsx`: stripped all `next/font/google` imports (causes hard build failure on corporate network).
- **Functional fixes**:
  - Search blocks while req lookup/skill extraction runs (`Wait for skill sync...`).
  - Request snapshot cloning prevents stale query summaries.
- **Playwright validation**: Desktop + mobile (390x844) flows passed.
- **Build**: `npm run build` + `npm run lint` pass (0 errors, 1 TanStack warning).

## Verified Running State
- Neo4j (Vagrant VM): `http://localhost:7474` / `bolt://localhost:7687` — 3315 nodes, 8558 rels, 14306 properties
- Embeddings: 1498 chunks, 1267 roles embedded; 1148 MENTIONS edges; 2 vector indexes
- FastAPI backend: `http://localhost:8000` — health check OK
- Smoke tests: 6/7 pass (other agent fixing 7/7)
- Search API: `POST /api/search {"req_number":"REQ-001","top_k":3}` returns ranked candidates with scores + evidence
- Frontend: `npm run build` passes, `npm run dev` serves at `http://localhost:3000`

## Operational Flow (Host)
1. `vagrant up`
2. `python scripts/03_build_graph_csv.py` (with `PYTHONPATH=.`)
3. `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"`
4. `PYTHONPATH=. python scripts/05_embed_chunks.py` (requires `GENESIS_SKLZ_API_KEY`)
5. `PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000`
6. `cd frontend && npm run dev`
7. `PYTHONPATH=. python scripts/06_smoke_test.py`

## Known Issues
- Smoke test 7/7 fails: empty `{}` payload returns 500 instead of 422 (other agent fixing).
- `GENESIS_SKLZ_API_KEY` not inherited by Git Bash — export manually: `export GENESIS_SKLZ_API_KEY="$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('GENESIS_SKLZ_API_KEY','User')" | tr -d '\r')"`
- `uvicorn` not on Git Bash PATH — use `python -m uvicorn`.
- All scripts need `PYTHONPATH=.` (no venv, no editable install).

## Archive
### Previous: Font & Typography Fix (2026-03-06)
- Removed broken Geist font variable references, replaced with system font stack.
- Bumped `text-xs` → `text-sm`/`text-base`, increased padding, reduced score decimals to `.toFixed(2)`.
- Superseded by corporate-tech refresh which rebuilt all styling from scratch.

### Previous: stable_id Bug Fix (2026-03-05)
- CSV builder wrote `stable_id` as `:ID` only — not as a property column. Fixed in all 5 node CSVs.
- Embed pipeline writes were no-ops until fix applied.

### Previous: Graph RAG Hybrid Retriever (2026-03-05)
- Two-stage Graph RAG: graph seed → filtered vector re-rank → batched LLM evidence.
- Created `hybrid_retriever.py`, 5 Cypher constants, entity linker, 7 unit tests.

### Previous: Vagrant + VirtualBox runtime (2026-03-05)
- Vagrantfile, provisioning, import scripts. Neo4j 5.26.21 validated.

## Session: Committed Playwright E2E Harness + Polish Pass (2026-03-06)
- **Goal**: Convert manual Playwright QA loop into committed, repeatable frontend e2e tests and apply one additional visual rhythm polish pass.
- **Scope completed**:
  - Added Playwright harness: `frontend/playwright.config.ts`, `frontend/e2e/app.spec.ts`.
  - Added frontend scripts: `test:e2e`, `test:e2e:headed`, `test:e2e:report`.
  - Updated `frontend/.gitignore` for Playwright artifacts and `frontend/README.md` with e2e usage.
  - Applied second-pass spacing/typography refinements in `page.tsx`, `SearchForm.tsx`, and evidence text in `CandidateTable.tsx`.
- **Deterministic test behavior**:
  - Tests mock `/api/postings`, `/api/extract-skills`, and `/api/search`; live backend is not required.
  - Async extraction delay is mocked to verify submit-button gating (`Wait for skill sync...`).
- **Verification**:
  - `npm.cmd run test:e2e` -> 3 passed.
  - `npm.cmd run build` -> pass.
  - `npm.cmd run lint` -> pass with 1 existing TanStack warning.
- **Environment note**:
  - Initial browser bootstrap required: `npx.cmd playwright install chromium`.
