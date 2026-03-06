# Progress

## Completed (2026-03-05)

### Reliability and contract hardening
- [x] Added centralized settings module: `src/config.py`.
- [x] Refactored API/pipeline modules to consume shared settings.
- [x] Added strict search request validation (`req_number`, `query_context`, bounded `top_k`, non-zero weights).
- [x] Added consistent error envelope and request ID middleware in `src/api/main.py`.
- [x] Added structured request logging with latency.

### Ranking and search quality
- [x] Added score normalization per pillar in `src/scoring/aggregator.py`.
- [x] Added normalized weight handling in aggregator.
- [x] Added per-pillar timings + total request timing.
- [x] Updated `/api/search` to resolve requisition context and include desired skills in query embedding text.

### Pipeline reliability
- [x] Added quality checks module: `src/pipeline/quality_checks.py`.
- [x] Updated phase scripts (01/02/03) to invoke reusable quality checks.
- [x] Updated Neo4j import path defaults to `data/exports/graph`.
- [x] Added import reuse mode (`--reuse-existing`) and safer import options.
- [x] Added embedding rebuild/index rebuild options in `scripts/05_embed_chunks.py`.
- [x] Added full orchestration script: `scripts/run_pipeline.py`.
- [x] Added env preflight validation: `scripts/validate_env.py`.

### Frontend behavior fixes
- [x] Added centralized frontend API URL module: `frontend/lib/apiConfig.ts`.
- [x] Updated req-number search flow to send `req_number` and posting context.
- [x] Added query summary card showing request context/weights/timing ID.
- [x] Added retry button and explicit loading/empty states.
- [x] Fixed candidate selection synchronization between table and score breakdown.

### Delivery gates
- [x] Added backend unit tests under `tests/`.
- [x] Added CI workflow: `.github/workflows/ci.yml`.
- [x] Added operator task runner: `scripts/tasks.ps1`.
- [x] Added canonical root runbook: `README.md`.
- [x] Updated script runbooks (`scripts/export_graph_csv.md`, `scripts/neo4j_bulk_import.md`).

### Vagrant + VirtualBox runtime (work machine path)
- [x] Added root `Vagrantfile` for disposable Neo4j VM (2 CPU / 4 GB).
- [x] Added VM provisioner: `scripts/vagrant/provision_neo4j.sh`.
- [x] Added fresh DB rebuild/import script: `scripts/vagrant/reset_and_import.sh`.
- [x] Added Vagrant helper doc: `scripts/vagrant/README.md`.
- [x] Updated root `README.md` with Vagrant-first quickstart and VirtualBox PATH note.
- [x] Added `.vagrant/` to `.gitignore`.
- [x] Added `vagrant-up` and `vagrant-reset` tasks in `scripts/tasks.ps1`.

## Verification
- [x] `python -m compileall src scripts tests`
- [x] `npm.cmd run lint` (warning only, no errors)
- [x] `npm.cmd run build`
- [x] Test functions invoked directly via `python -c` to validate new unit tests in absence of local pytest module
- [x] `vagrant validate`
- [x] Bash syntax checks for `scripts/vagrant/*.sh`
- [x] `vagrant provision` completed on VirtualBox VM
- [x] `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"` completed with successful import and count verification
- [x] Host connectivity checks (`http://localhost:7474`, `bolt://localhost:7687`)

### Documentation and memory-bank synchronization (2026-03-05)
- [x] Updated `docs/README.md` to state Vagrant-first Neo4j flow and Docker alternate.
- [x] Updated `scripts/neo4j_bulk_import.md` with Vagrant import command, Docker fallback, and Neo4j 5.26 CLI syntax note.
- [x] Rewrote `memory-bank/techContext.md` with validated runtime state (Neo4j 5.26.21, host endpoints, import counts, Vagrant scripts).
- [x] Rewrote `memory-bank/systemPatterns.md` with Vagrant import pattern and corporate TLS bootstrap fallback.
- [x] Added `docs/discoveries/06-local-vagrant-runtime-validation.md` and indexed it in `docs/discoveries/README.md`.

### Bug fix: stable_id missing from Neo4j node properties
- [x] Diagnosed: CSV builder wrote `stable_id` as `:ID` column only — not as a property column.
- [x] Fixed `src/pipeline/load/graph_csv_builder.py` to include `stable_id` as explicit property in all 5 node CSVs.
- [x] Rebuilt CSVs via `python scripts/03_build_graph_csv.py`.
- [x] Re-imported into Vagrant Neo4j — 3315 nodes, 8558 rels, 14306 properties (up from ~11k).
- [x] Re-ran `python scripts/05_embed_chunks.py` — 1498 chunks, 1267 roles embedded, 1148 MENTIONS edges created.

### End-to-end verification
- [x] FastAPI backend started: `python -m uvicorn src.api.main:app --reload --port 8000`
- [x] Smoke tests: 6/7 pass (`python scripts/06_smoke_test.py`)
- [x] Search API tested: `POST /api/search {"req_number":"REQ-001","top_k":3}` — returns ranked candidates with evidence

## Verification
- [x] `python -m compileall src scripts tests`
- [x] `npm.cmd run lint` (warning only, no errors)
- [x] `npm.cmd run build`
- [x] Test functions invoked directly via `python -c` to validate new unit tests in absence of local pytest module
- [x] `vagrant validate`
- [x] Bash syntax checks for `scripts/vagrant/*.sh`
- [x] `vagrant provision` completed on VirtualBox VM
- [x] `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"` completed
- [x] Host connectivity checks (`http://localhost:7474`, `bolt://localhost:7687`)
- [x] Embedding pipeline: 1498 chunks, 1267 roles, 1148 MENTIONS, 2 vector indexes
- [x] Smoke tests: 6/7 pass
- [x] Search API returns ranked candidates with composite scores and LLM-generated evidence

### Graph RAG Hybrid Retriever (2026-03-05)
- [x] Created `src/graph/hybrid_retriever.py` — two-stage Graph RAG: graph seed → filtered vector re-rank → batched LLM evidence
- [x] Added `MENTIONS = "MENTIONS"` to `src/graph/schema.py`
- [x] Added 5 Cypher constants to `src/graph/queries.py`: `POSTING_GRAPH_SEED`, `SKILL_LIST_GRAPH_SEED`, `CHUNK_VECTOR_FILTERED`, `ROLE_VECTOR_FILTERED`, `PERSON_CHUNK_EVIDENCE`
- [x] Added `_link_chunk_to_skills()`, `link_chunk_mentions()`, `_clear_mentions_edges()` to `src/pipeline/embed/embed_pipeline.py`
- [x] Added `--rebuild-mentions` flag to `scripts/05_embed_chunks.py`
- [x] Refactored `src/scoring/aggregator.py` to delegate to `HybridRetriever`; added `posting_req_number` + `use_llm_evidence` keyword-only params
- [x] Updated `src/api/routers/search.py` to pass `posting_req_number=payload.req_number` to `aggregate()`
- [x] Created `tests/test_hybrid_retriever.py` — 7 unit tests for entity linker, all PASS
- [x] All files compile clean; existing aggregator helper tests still pass

### Frontend font & typography readability fix (2026-03-06)
- [x] Removed broken Geist font references from `globals.css` (variables never defined).
- [x] Replaced `next/font/google` Inter import with system font stack in `globals.css` — `next/font/google` causes hard build failure on corporate network.
- [x] Set base `font-size: 16px` and `line-height: 1.5` on body.
- [x] Bumped `text-xs` → `text-sm`/`text-base` across all components (page.tsx, SearchForm, CandidateTable, ScoreBreakdown, SkillEditor).
- [x] Increased table cell padding (`px-3 py-2` → `px-4 py-3`), table headers from `text-xs` to `text-sm`.
- [x] Reduced score display precision from `.toFixed(3)` to `.toFixed(2)`.
- [x] Added `shadow-sm` + `border border-gray-200` to card containers.
- [x] Increased button touch targets (`py-2` → `py-2.5`) and input padding.
- [x] Chart tick font size bumped from 11px to 13px.
- [x] `npm run build` passes, `npm run lint` passes (0 errors).

### Frontend corporate-tech style implementation + iterative Playwright validation (2026-03-06)
- [x] Replaced generic prototype styling with a tokenized corporate palette and layered background in `frontend/app/globals.css`.
- [x] Refactored top-level page shell in `frontend/app/page.tsx` (hero/status panel, improved summary, stronger state surfaces).
- [x] Reworked search and skills UX in `frontend/components/SearchForm.tsx` and `frontend/components/SkillEditor.tsx`.
- [x] Modernized results table interactions and visual hierarchy in `frontend/components/CandidateTable.tsx`.
- [x] Restyled and hardened score visualization card in `frontend/components/ScoreBreakdown.tsx`.
- [x] Fixed async race by disabling search while extraction/lookup is running (`Wait for skill sync...` state).
- [x] Ensured summary consistency via submit-time request snapshot cloning in `page.tsx`.
- [x] Playwright desktop flow checks passed: req load, search, table render, row evidence, sort interactions.
- [x] Playwright role-description flow checks passed: extraction gating, search completion, summary count correctness.
- [x] Playwright mobile check passed at `390x844` with verified horizontal table scrollability.
- [x] `npm.cmd run build` succeeded.
- [x] `npm.cmd run lint` succeeded with one existing warning (`react-hooks/incompatible-library` from TanStack `useReactTable`).
- [x] Removed `next/font/google` imports (IBM Plex Sans, Space Grotesk) from `layout.tsx` — prevents hard build failure on corporate network.
- [x] Build re-verified after layout.tsx fix: `npm run build` passes, `npm run lint` 0 errors.

## Outstanding
- [ ] Install pytest in the active Python environment and run `python -m pytest -q tests`.
- [ ] Fix smoke test 7/7: empty payload returns 500 instead of 422 (other agent in progress).
- [ ] Commit all accumulated work to git (other agent in progress).
- [ ] Launch frontend + backend together and verify end-to-end UI flow.
- [ ] Re-run `python scripts/06_smoke_test.py` against live API to verify hybrid retriever integration.

### Frontend Playwright e2e automation and polish pass (2026-03-06)
- [x] Added Playwright dependency and scripts in `frontend/package.json`.
- [x] Added `frontend/playwright.config.ts` with reusable local web-server strategy.
- [x] Added deterministic mocked-flow e2e specs in `frontend/e2e/app.spec.ts`.
- [x] Added Playwright artifact ignores in `frontend/.gitignore`.
- [x] Updated `frontend/README.md` with e2e usage notes.
- [x] Applied second-pass visual rhythm refinements in `frontend/app/page.tsx`, `frontend/components/SearchForm.tsx`, and `frontend/components/CandidateTable.tsx`.
- [x] Installed browser runtime via `npx.cmd playwright install chromium`.
- [x] Validation: `npm.cmd run test:e2e` -> 3 passed.
- [x] Validation: `npm.cmd run build` succeeded.
- [x] Validation: `npm.cmd run lint` succeeded (1 existing warning from TanStack `useReactTable`).
