# Implementation Plan: Get Prototype Running End-to-End

[Overview]
Fix three critical bugs, run the full data pipeline, start all services, and verify end-to-end functionality with Playwright.

The prototype code is 95% complete (8 phases committed). Three bugs prevent the FastAPI app from starting: `src/api/routers/skills.py` is missing entirely, the search router has a type mismatch with `AggregateOutput`, and `SearchResponse` is missing required fields. Once these are fixed, the pipeline needs to be run (Neo4j import + embeddings), services started, and the full UI flow verified with Playwright.

The SKLZ API (https://aihr-sklz.us.lmco.com/sklz/api) is available as a real data source. The hackathon prototype currently uses synthetic data, which is fine for the demo. The skills.py router uses Genesis dual-LLM (Claude for intent → GPT for structured JSON), with a graceful regex fallback if Genesis is unavailable.

[Types]
No new types needed — existing Pydantic models in `src/api/models.py` are correct and just need the routers to populate all fields.

Existing relevant types:
- `SearchResponse` (models.py): requires `request_id: str`, `candidates: list[CandidateResult]`, `query_skills_used: list[str]`, `timings_ms: dict[str, float]`
- `AggregateOutput` (aggregator.py): dataclass with `candidates: list[CandidateResult]`, `timings_ms: dict[str, float]`
- `SearchWeights` (models.py): Pydantic model with `.normalized()` method returning `dict[str, float]`
- `SkillExtractionRequest` / `SkillExtractionResponse` (models.py): already defined, just needs the router

[Files]
Three files need fixes and one new file must be created.

New files to create:
- `src/api/routers/skills.py` — POST /api/extract-skills endpoint using Genesis dual-LLM (Claude reasoning → GPT JSON extraction), with keyword fallback

Existing files to modify:
- `src/api/routers/search.py` — unpack `AggregateOutput.candidates` and `AggregateOutput.timings_ms`; populate `request_id` (UUID4); convert `SearchWeights` to dict via `.normalized()`
- `src/scoring/aggregator.py` — fix `_normalize_weights()` to accept both dict and `SearchWeights` Pydantic model (call `.normalized()` if Pydantic model)

Files NOT changing:
- `src/api/main.py` — already registers all three routers correctly
- `src/api/models.py` — already correct
- All scoring pillars — no changes needed
- Frontend — no changes needed
- `docker-compose.yml` — already correct

[Functions]
New and modified functions needed.

New functions in `src/api/routers/skills.py`:
- `extract_skills(request: SkillExtractionRequest) -> SkillExtractionResponse` — POST /api/extract-skills handler; calls `_extract_with_genesis()`, falls back to `_extract_keywords()` on failure
- `_extract_with_genesis(text: str) -> dict` — dual-LLM: Claude (claude-4-5-sonnet-latest) for reasoning prompt → GPT (gpt-oss-120b) for `json_schema` structured output returning `{required_skills: [...], desired_skills: [...]}`
- `_extract_keywords(text: str) -> dict` — regex fallback: finds "must have/required: ..." and "nice to have/desired: ..." patterns, returns same shape

Modified functions:
- `search_candidates()` in `src/api/routers/search.py`:
  - Change: `results = aggregate(...)` → unpack as `output = aggregate(...)`, then use `output.candidates` and `output.timings_ms`
  - Change: add `import uuid` and generate `request_id = str(uuid.uuid4())`  
  - Change: pass `weights=request.weights.normalized()` to `aggregate()` instead of `request.weights` directly
  - Change: populate `SearchResponse(request_id=request_id, candidates=candidates, query_skills_used=..., timings_ms=output.timings_ms)`

- `_normalize_weights()` in `src/scoring/aggregator.py`:
  - Change: accept `weights: dict[str, float] | Any | None` — if it has `.normalized()` method (Pydantic model), call it; otherwise treat as dict
  - Alternative (simpler): just fix the call site in search.py to pass `.normalized()` dict — this is the preferred approach

[Classes]
No class changes needed. All existing classes/dataclasses are correct.

[Dependencies]
No new Python or Node dependencies needed. All required packages are already in `pyproject.toml`:
- `openai` — Genesis SDK (already installed)
- `httpx` — already installed
- `neo4j` — already installed
- `fastapi`, `uvicorn` — already installed

Runtime requirements (must be set before running):
- `GENESIS_SKLZ_API_KEY` env var — for embeddings and skill extraction
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` — defaults work with docker-compose
- `SSL_CERT_FILE` = `C:/Users/e477258/combined_pem.pem`
- Docker running with `neo4j-prototype` container

[Testing]
Playwright MCP is used to verify the full UI flow after all fixes and services are running.

Test sequence:
1. Health check: GET http://localhost:8000/ → `{"status": "ok"}`
2. Extract skills: POST /api/extract-skills with job description text → returns skill lists
3. Load req: GET /api/postings/REQ-001 → returns posting with skills  
4. Search: POST /api/search with role_title + required_skills → 10 candidates returned
5. Playwright: Launch http://localhost:3000, interact with SearchForm, verify CandidateTable renders, click a row, verify evidence expansion, verify ScoreBreakdown chart renders

Smoke test script: `python scripts/06_smoke_test.py` (7 test cases, already written)

[Implementation Order]
Implement fixes atomically, then run pipeline, then verify.

1. Create `src/api/routers/skills.py` — missing router (app won't import without this)
2. Fix `src/api/routers/search.py` — unpack AggregateOutput, add UUID request_id, use weights.normalized()
3. Verify API starts: `uvicorn src.api.main:app --reload --port 8000` (quick start test)
4. Start Neo4j: `docker compose up -d neo4j` and wait for health
5. Run `python scripts/04_neo4j_import.py` — import graph data (CSVs already exist in data/exports/graph/)
6. Run `python scripts/05_embed_chunks.py` — embed chunks/roles, create vector indexes
7. Start uvicorn in background terminal
8. Start Next.js: `cd frontend && npm run dev`
9. Run smoke test: `python scripts/06_smoke_test.py`
10. Playwright end-to-end UI test: launch http://localhost:3000, test full search flow
