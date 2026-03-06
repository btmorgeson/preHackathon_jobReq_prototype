# Discovery 03: Codebase Architecture

> **Date**: March 5, 2026  
> **Author**: Cline AI (investigation session)  
> **Purpose**: Comprehensive map of what has been built, what works, and what's wired together

---

## Project Overview

**Goal**: HR AI Hackathon (March 23-26, 2026) — Job Requisition → Candidate Ranking system  
**Stack**: Python FastAPI backend + Next.js frontend + Neo4j graph database + Genesis AI (LMCO LLM gateway)

---

## Directory Structure

```
preHackathon_jobReq_prototype/
│
├── src/                          ← Python backend
│   ├── api/                      ← FastAPI application
│   │   ├── main.py               ← App factory, CORS, router mounting
│   │   ├── deps.py               ← FastAPI dependency injection (get_driver)
│   │   ├── models.py             ← Pydantic request/response models
│   │   └── routers/
│   │       ├── search.py         ← POST /api/search (main ranking endpoint)
│   │       ├── postings.py       ← GET /api/postings/{req_number}
│   │       └── skills.py         ← POST /api/skills/extract-skills
│   │
│   ├── scoring/                  ← Three-pillar scoring system
│   │   ├── aggregator.py         ← Orchestrates all three pillars
│   │   ├── skill_pillar.py       ← Exact skill matching (weight: 0.4)
│   │   ├── role_history_pillar.py ← Role/title vector search (weight: 0.3)
│   │   └── experience_pillar.py  ← Chunk embedding search (weight: 0.3)
│   │
│   ├── graph/
│   │   ├── queries.py            ← All Cypher query strings as constants
│   │   └── schema.py             ← Node/relationship definitions
│   │
│   ├── pipeline/                 ← Data ingestion pipeline
│   │   ├── fetch/onet_fetcher.py ← Download O*NET occupational data
│   │   ├── transform/
│   │   │   ├── normalize.py      ← Data normalization utilities
│   │   │   └── synthetic_employees.py ← Generate 500 fake employees
│   │   ├── load/
│   │   │   ├── graph_csv_builder.py ← Build CSV files for Neo4j import
│   │   │   └── neo4j_setup.py    ← Neo4j schema/index creation
│   │   └── embed/
│   │       ├── genesis_client.py ← Genesis AI embedding client
│   │       └── embed_pipeline.py ← Generate and store embeddings
│   │
│   └── config.py                 ← Centralized settings via env vars
│
├── frontend/                     ← Next.js 15 + TypeScript + Tailwind
│   ├── app/
│   │   ├── page.tsx              ← Main search page
│   │   ├── layout.tsx            ← Root layout
│   │   └── globals.css           ← Global styles
│   ├── components/
│   │   ├── SearchForm.tsx        ← Job req input form
│   │   ├── CandidateTable.tsx    ← Ranked results table
│   │   ├── ScoreBreakdown.tsx    ← Per-pillar score visualization
│   │   └── SkillEditor.tsx       ← Editable skills list
│   └── lib/
│       └── apiConfig.ts          ← API base URL configuration
│
├── scripts/                      ← CLI pipeline scripts
│   ├── 01_fetch_onet.py          ← Fetch O*NET data
│   ├── 02_generate_employees.py  ← Generate synthetic employee data
│   ├── 03_build_graph_csv.py     ← Export graph CSV for Neo4j import
│   ├── 04_neo4j_import.py        ← Import CSVs into Neo4j (uses docker)
│   ├── 05_embed_chunks.py        ← Embed text chunks via Genesis
│   ├── 06_smoke_test.py          ← End-to-end validation
│   ├── run_pipeline.py           ← Orchestrated full pipeline runner
│   ├── validate_env.py           ← Check required env vars
│   └── test_genesis_connection.py ← Verify Genesis AI connectivity
│
├── data/                         ← Data layer (gitignored content)
│   ├── raw/onet/onet_data.json   ← ✅ EXISTS: O*NET occupational data
│   ├── parquet/                  ← ✅ EXISTS: 6 parquet files
│   │   ├── persons.parquet       ← 500 synthetic employees
│   │   ├── roles.parquet         ← 1,267 job roles
│   │   ├── skills.parquet        ← 40 skill types
│   │   ├── postings.parquet      ← 10 job postings (REQ-001 to REQ-010)
│   │   ├── chunks.parquet        ← 1,498 text chunks
│   │   └── person_skills.parquet ← Employee-skill mappings
│   ├── exports/graph/            ← ✅ EXISTS: nodes/ and edges/ subdirs
│   └── embeddings/               ← (empty — not yet generated)
│
├── docs/                         ← Documentation
├── tests/                        ← pytest test files
├── memory-bank/                  ← Cline AI context memory
├── docker-compose.yml            ← Local Neo4j (if running locally)
└── pyproject.toml                ← Python project config + dependencies
```

---

## The Three-Pillar Scoring System

This is the heart of the application. Each candidate receives three subscores that combine into a composite ranking.

```
SearchRequest (req_number or free text)
    │
    ▼
Genesis AI Embedding (mxbai-embed-large-v1, 1024-dim)
    │
    ├──► Skill Pillar (weight: 0.4)
    │        └── Exact string match: Employee skills vs. required/desired skills
    │
    ├──► Role History Pillar (weight: 0.3)
    │        └── Vector search: role_title_idx → find similar past roles
    │            + Recency decay (RECENCY_DECAY = 0.85 per position)
    │
    └──► Experience Pillar (weight: 0.3)
             └── Vector search: chunk_embedding_idx → find relevant text chunks
    
    ▼
Normalize each pillar (min-max scaling across candidate pool)
    │
    ▼
Composite = 0.4×skill + 0.3×role + 0.3×experience
    │
    ▼
Return top_k CandidateResult objects (sorted DESC)
```

### Weights Are Adjustable

The `SearchWeights` model allows per-request weight overrides:

```json
{
  "req_number": "REQ-001",
  "weights": {
    "skill": 0.5,
    "role": 0.3,
    "experience": 0.2
  }
}
```

Weights are auto-normalized to sum to 1.0.

---

## API Endpoints

### `POST /api/search`

**The main ranking endpoint.**

**Request body** (`SearchRequest`):
```json
{
  "req_number": "REQ-001",           // Optional: lookup posting by ID
  "role_title": "Software Engineer", // Optional: free-text title
  "role_description": "...",          // Optional: free-text description
  "required_skills": ["Python", "ML"], // Optional: explicit skills
  "desired_skills": ["FastAPI"],        // Optional
  "weights": {"skill": 0.4, "role": 0.3, "experience": 0.3},
  "top_k": 10
}
```

**Response** (`SearchResponse`):
```json
{
  "request_id": "uuid",
  "candidates": [
    {
      "person_stable_id": "P-0001",
      "name": "Jane Doe",
      "current_title": "Senior Engineer",
      "composite_score": 0.8234,
      "skill_score": 0.9,
      "role_score": 0.75,
      "experience_score": 0.82,
      "evidence": "Text snippet showing relevant experience...",
      "matched_skills": ["Python", "Machine Learning"]
    }
  ],
  "query_skills_used": ["Python", "ML", "FastAPI"],
  "timings_ms": {"skill": 12.3, "role": 45.2, "experience": 88.1, "total": 145.6}
}
```

### `GET /api/postings/{req_number}`

Fetch a job posting with its required/desired skills.

### `POST /api/skills/extract-skills`

Extract skills from free text using Genesis AI (Claude → GPT dual-LLM pattern).

**Request**: `{"text": "Looking for a Python developer with ML experience..."}`  
**Response**: `{"required_skills": ["Python"], "desired_skills": ["Machine Learning"]}`

---

## Genesis AI Integration (Dual-LLM Pattern)

The key insight: Claude fails on `json_schema` response format (returns 500) → use GPT for structured JSON extraction.

```python
# Step 1: Claude (claude-4-5-sonnet-latest) for reasoning
reasoning_response = client.chat.completions.create(
    model="claude-4-5-sonnet-latest",
    messages=[{"role": "user", "content": f"Extract skills from: {text}"}]
)

# Step 2: GPT (gpt-oss-120b) for structured JSON extraction
extraction_response = client.chat.completions.create(
    model="gpt-oss-120b",
    response_format={"type": "json_schema", "json_schema": SKILL_SCHEMA},
    messages=[
        {"role": "system", "content": "Extract structured data..."},
        {"role": "user", "content": reasoning_response.choices[0].message.content}
    ]
)
```

The Genesis client is configured in `src/pipeline/embed/genesis_client.py`:
- Base URL: `https://api.ai.us.lmco.com/v1`  
- Organization header: `openai-organization: SKLZ`
- SSL cert: `C:/Users/e477258/combined_pem.pem`

---

## What Was Built in Previous Sessions

### ✅ Completed and Verified

1. **`src/api/routers/skills.py`** — Was MISSING (caused 500 on app startup). Fully created with dual-LLM + keyword regex fallback.

2. **`src/api/routers/search.py`** — Fixed multiple bugs:
   - Added `import uuid` and `request_id = str(uuid4())`
   - Fixed type mismatch: `aggregate()` returned `AggregateOutput` (not list)
   - Fixed weights: now passes `payload.weights.normalized()` dict
   - Returns full `SearchResponse`

3. **Import test PASSED**:
   ```
   python -c "from src.api.routers import skills, search, postings; print('All routers import OK')"
   → All routers import OK
   ```

4. **Synthetic data generated** (scripts 01–03):
   - 500 synthetic persons (Parquet)
   - 1,267 roles
   - 40 skills
   - 10 job postings (REQ-001 to REQ-010)
   - 1,498 text chunks

5. **Graph CSV exports** exist in `data/exports/graph/`

### ❌ Not Yet Done

1. **Embeddings**: `data/embeddings/` is empty — script 05 not run
2. **Neo4j import**: Synthetic data not imported into any Neo4j instance  
   - Script 04 uses `docker cp` + `neo4j-admin` — requires Docker locally (not installed)
3. **Backend not started**: `uvicorn src.api.main:app` hasn't been launched yet
4. **Frontend not started**: `cd frontend && npm run dev` not run
5. **Smoke test**: Script 06 hasn't run

---

## Known Bug: Script 04 Requires Docker

`scripts/04_neo4j_import.py` uses `docker cp` to copy CSV files into a running Neo4j container and then calls `neo4j-admin database import`. This **requires Docker to be installed locally**.

**Docker is NOT installed** on this machine.

**Workarounds**:
1. Use Python `neo4j` driver to load data directly via Cypher `CREATE` statements
2. Use the Vagrant VM in `model-api/` (has Docker) and SSH in
3. Use Neo4j 5.x instance at `140.169.17.216` if accessible
4. Use the real SKLZ data at `140.169.17.180` instead of importing synthetic data

---

## pyproject.toml Dependencies

```toml
[tool.uv.sources]
dependencies = [
    "fastapi",
    "uvicorn",
    "neo4j",
    "pydantic",
    "openai",       # Used for Genesis AI (OpenAI-compatible API)
    "httpx",
    "pandas",
    "pyarrow",
    "python-dotenv",
]
```

---

## Frontend Architecture

Built with **Next.js 15** (App Router) + **TypeScript** + **Tailwind CSS**.

### Key Components

| Component | Purpose |
|-----------|---------|
| `SearchForm.tsx` | Input form for job req search (req_number, skills, weights) |
| `CandidateTable.tsx` | Ranked results with composite score + name + title |
| `ScoreBreakdown.tsx` | Visual breakdown of skill/role/experience subscores |
| `SkillEditor.tsx` | Editable chip list for required/desired skills |

### API Configuration

`frontend/lib/apiConfig.ts` sets the backend base URL:
```typescript
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
```

The frontend calls `http://localhost:8000/api/search` etc.

---

## Test Files

```
tests/
├── test_api_models.py       ← Pydantic model validation tests
├── test_quality_checks.py   ← Pipeline data quality checks
└── test_scoring_aggregator.py ← Scoring aggregator unit tests
```

Run with: `python -m pytest tests/ -v`

---

## Configuration: `src/config.py`

All settings pulled from environment variables with sensible defaults:

| Setting | Env Var | Default |
|---------|---------|---------|
| Neo4j URI | `NEO4J_URI` | `bolt://localhost:7687` |
| Neo4j User | `NEO4J_USER` | `neo4j` |
| Neo4j Password | `NEO4J_PASSWORD` | `password12345` |
| Genesis API Key | `GENESIS_SKLZ_API_KEY` | None |
| Genesis Base URL | `GENESIS_BASE_URL` | `https://api.ai.us.lmco.com/v1` |
| Genesis Org | `GENESIS_ORG` | `SKLZ` |
| Reasoning Model | `GENESIS_REASONING_MODEL` | `claude-4-5-sonnet-latest` |
| Extraction Model | `GENESIS_EXTRACTION_MODEL` | `gpt-oss-120b` |
| Embedding Model | `GENESIS_EMBEDDING_MODEL` | `mxbai-embed-large-v1` |
| Default top_k | `SEARCH_DEFAULT_TOP_K` | `10` |
| Max top_k | `SEARCH_MAX_TOP_K` | `50` |

Settings are cached via `@lru_cache(maxsize=1)` — read once at startup.
