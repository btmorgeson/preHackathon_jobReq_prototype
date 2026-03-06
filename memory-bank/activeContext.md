# Active Context

## Current Task
Project is demo-ready (2026-03-06). No active task.
Claude Code project config added: `.claude/settings.local.json` + agents `neo4j` and `pipeline`.

## Last Completed Session: Frontend Corporate-Tech Refresh + Playwright QA (2026-03-06)
- Tokenized corporate palette, layered background, refreshed all 4 components + page shell.
- Local font stacks (no `next/font/google`). Async UX guard + request snapshot cloning.
- Playwright desktop + mobile (390x844) validated. Build + lint pass.

## Verified Running State
- Neo4j (Vagrant VM): `http://localhost:7474` / `bolt://localhost:7687` — 3315 nodes, 8558 rels, 14306 properties
- Embeddings: 1498 chunks, 1267 roles embedded; 1148 MENTIONS edges; 2 vector indexes
- FastAPI backend: `http://localhost:8000` — health check OK
- Smoke tests: 6/7 pass live (7/7 verified via TestClient; server restart needed for live 7/7)
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
- Smoke test 7/7: 422 fix committed; verified via TestClient + pytest. Live server needs restart to pick up the change.
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

### Previous: Playwright E2E Harness + Polish Pass (2026-03-06)
- Committed Playwright harness: `frontend/playwright.config.ts`, `frontend/e2e/app.spec.ts`.
- Added `test:e2e`, `test:e2e:headed`, `test:e2e:report` scripts. 3 mocked-flow specs pass.
- Second-pass spacing/typography refinements applied. Build + lint verified.
- First-time browser install: `npx.cmd playwright install chromium`.
