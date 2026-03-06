# Implementation Plan: Job Req → Candidate Ranking Prototype

## Context

The project is a pre-hackathon prototype for an internal talent-matching system. Given a job requisition or role description, it returns a ranked list of synthetic "employees" with supporting evidence. The final demo is for the LMCO HR AI Hackathon (March 23–26, 2026).

**Simplifications agreed:**
- No Iceberg/Spark/MinIO — Neo4j + Python only
- Synthetic employee data (O*NET + PUMS + Faker) — no real Atlas data
- Genesis API embeddings: `mxbai-embed-large-v1` (1024-dim, cosine) — **not Bedrock**
- Frontend: FastAPI (backend) + Next.js (frontend)

**LLM Backend: Genesis API (primary)**
- Reasoning: `claude-4-5-sonnet-latest` via Genesis
- Structured extraction: `gpt-oss-120b` via Genesis (Claude returns HTTP 500 on json_schema)
- Embeddings: `mxbai-embed-large-v1` via Genesis
- Bedrock: fallback only (not used for primary workflow)

---

## Architecture Overview

```
O*NET API → synthetic employee generator → parquet files
                                               ↓
                                     graph CSV export (nodes + edges)
                                               ↓
                                     neo4j-admin bulk import
                                               ↓
                             Genesis embed — mxbai-embed-large-v1 (Chunks + Roles)
                                               ↓
                                        Neo4j vector indexes
                                               ↓
                      FastAPI scoring engine (3 pillars → composite score)
                                               ↓
                                        Next.js frontend
```

## Graph Schema

```
(Person {stable_id, name, current_title})
  -[:HAS_ROLE {start_date, end_date, is_current}]->
(Role {stable_id, title, title_embedding, soc_code})

(Person)-[:HAS_SKILL]->(Skill {stable_id, name})

(Person)-[:HAS_CHUNK]->(Chunk {stable_id, text, embedding, chunk_type})
  # chunk_type: "summary" | "closeout"

(Posting {stable_id, req_number, title, description})
  -[:REQUIRES_SKILL {required: true/false}]->(Skill)

(Chunk)-[:MENTIONS]->(Skill)
(Chunk)-[:MENTIONS]->(Role)
```

---

## Project Structure

```
src/
  pipeline/
    fetch/
      onet_fetcher.py       # O*NET API: occupations, skills, work summaries
      usajobs_fetcher.py    # USAJOBS: sample postings for req lookup
    transform/
      synthetic_employees.py  # Generate N fake employees via Faker + O*NET data
      normalize.py            # Canonical field builder (stable_id, etc.)
    load/
      graph_csv_builder.py  # Emit nodes/edges CSVs
      neo4j_setup.py        # Constraints + indexes + bulk import orchestration
    embed/
      genesis_client.py     # Batched embedding calls (Genesis mxbai-embed-large-v1)
      embed_pipeline.py     # Chunks + Role titles → embeddings → write to Neo4j
  graph/
    queries.py              # All named Cypher queries
    schema.py               # Node/edge label constants
  scoring/
    skill_pillar.py         # Skill Evidence scoring
    role_history_pillar.py  # Role History scoring (recency-weighted)
    experience_pillar.py    # Experience Evidence scoring (vector search)
    aggregator.py           # Combine 3 pillars → composite score + evidence
  api/
    main.py                 # FastAPI app
    models.py               # Pydantic request/response models
    routers/
      search.py             # POST /api/search
      postings.py           # GET /api/postings/{req_number}
      skills.py             # POST /api/extract-skills
frontend/
  src/app/                  # Next.js App Router
  src/components/
    SearchForm.tsx          # Req number OR role description + skill chips
    SkillEditor.tsx         # Extracted skills shown as editable chips
    CandidateTable.tsx      # Ranked results with expandable evidence rows
    ScoreBreakdown.tsx      # Bar chart: skill / role_history / experience scores
scripts/
  01_fetch_onet.py          # Pull O*NET occupation/skill data → data/raw/
  02_generate_employees.py  # Synthetic employees → data/parquet/employees.parquet
  03_build_graph_csv.py     # parquet → node/edge CSVs → data/exports/graph/
  04_neo4j_import.py        # Constraints, bulk import, verify
  05_embed_chunks.py        # Embed Chunks + Roles → write to Neo4j nodes
  06_smoke_test.py          # End-to-end: query → ranked results
data/
  raw/onet/                 # O*NET JSON responses
  raw/usajobs/              # USAJOBS sample postings
  parquet/                  # employees.parquet, roles.parquet, skills.parquet
  exports/graph/            # nodes/*.csv, edges/*.csv
.env.example
pyproject.toml              # Python dependencies
```

---

## Implementation Phases

### Phase 1: Data Foundation (Python pipeline)

**1a. O*NET Fetcher** (`src/pipeline/fetch/onet_fetcher.py`)
- Hit O*NET Web Services API (free, no auth required for basic endpoint)
- Fetch: occupations list, skills by SOC code, work activity summaries
- Save to `data/raw/onet/*.json`

**1b. Synthetic Employee Generator** (`src/pipeline/transform/synthetic_employees.py`)
- Generate 500–1000 `Person` records using Faker (name, employee_id)
- Assign 1–4 `Role` records per person from O*NET occupations (most recent = current)
- Assign 5–15 `Skill` records per person from O*NET skills for their occupation
- Generate a `summary` Chunk: template from O*NET work summary text
- Generate 1–3 `closeout` Chunks: template sentences about achievements
- Apply recency dates (start/end) to role history
- Output: `data/parquet/{employees,roles,skills,chunks}.parquet`

**1c. Normalization**
- `stable_id = sha256(source_system + '|' + source_id + '|' + version)`
- `source_system = "synthetic_onet"` for generated data
- `ingested_at = datetime.utcnow().isoformat()`

### Phase 2: Graph Build

**2a. Graph CSV Builder** (`scripts/03_build_graph_csv.py`)
- Node CSVs: `persons.csv`, `roles.csv`, `skills.csv`, `chunks.csv`, `postings.csv`
- Edge CSVs: `person_has_role.csv`, `person_has_skill.csv`, `person_has_chunk.csv`, `role_requires_skill.csv`, `chunk_mentions_skill.csv`
- Headers follow neo4j-admin import format (`:ID`, `:START_ID`, `:END_ID`, `:LABEL`, `:TYPE`)

**2b. Neo4j Setup** (`scripts/04_neo4j_import.py`)
- Copy CSVs into `neo4j_import` volume (`docker cp`)
- Run `neo4j-admin database import full` inside container
- Create uniqueness constraints: `Person.stable_id`, `Skill.name`, etc.
- Create BM25 full-text index on `Skill.name` and `Role.title`
- Confirm node/rel counts

### Phase 3: Embeddings

**3a. Genesis Client** (`src/pipeline/embed/genesis_client.py`)
- Model: `mxbai-embed-large-v1` (1024 dims, cosine)
- SDK: `openai` Python package (OpenAI-compatible interface)
- Base URL: `https://api.ai.us.lmco.com/v1`, org header `openai-organization: SKLZ`
- API key: `GENESIS_SKLZ_API_KEY` env var
- Batch size: 25 texts per call
- SSL: `httpx.Client(verify="C:/Users/e477258/combined_pem.pem")` passed to OpenAI client
- Retry with exponential backoff on rate limit errors
- **NOT Bedrock** — boto3 not required for embeddings

**3b. Embed Pipeline** (`scripts/05_embed_chunks.py`)
- Embed all `Chunk.text` → write to `Chunk.embedding` property
- Embed all `Role.title` → write to `Role.title_embedding` property
- Create vector index: `CALL db.index.vector.createNodeIndex('chunk_embedding_idx', 'Chunk', 'embedding', 1024, 'cosine')`
- Create vector index: `CALL db.index.vector.createNodeIndex('role_title_idx', 'Role', 'title_embedding', 1024, 'cosine')`

### Phase 4: Scoring Engine

**Skill Evidence Pillar** (`src/scoring/skill_pillar.py`)
```python
# Embed query skill list → compare cosine sim against candidate skill embeddings
# Aggregate: weighted sum (required skills weight 2x desired)
# Output: score 0.0–1.0
```

**Role History Pillar** (`src/scoring/role_history_pillar.py`)
```cypher
CALL db.index.vector.queryNodes('role_title_idx', 200, $queryEmbedding)
YIELD node AS role, score
MATCH (p:Person)-[r:HAS_ROLE]->(role)
WITH p, collect({score: score, end_date: r.end_date}) AS role_scores
RETURN p.stable_id, role_scores
```
- Apply recency decay: `score * (0.8 ^ position_from_most_recent)`
- Take max across roles per person

**Experience Evidence Pillar** (`src/scoring/experience_pillar.py`)
```cypher
CALL db.index.vector.queryNodes('chunk_embedding_idx', 500, $queryEmbedding)
YIELD node AS chunk, score
MATCH (p:Person)-[:HAS_CHUNK]->(chunk)
RETURN p.stable_id, avg(score) AS exp_score
ORDER BY exp_score DESC LIMIT 50
```

**Aggregator** (`src/scoring/aggregator.py`)
```python
composite = w_skill * skill_score + w_role * role_score + w_exp * exp_score
# Default weights: skill=0.4, role=0.3, experience=0.3 (user-adjustable)
```
Returns: `List[CandidateResult]` sorted by composite score, with evidence snippets.

### Phase 5: FastAPI Backend

**Endpoints:**
```
POST /api/search
  In:  SearchRequest(req_number?, role_title?, role_description?, required_skills?, desired_skills?, weights?)
  Out: SearchResponse(candidates: List[CandidateResult], query_context)

GET  /api/postings/{req_number}
  Out: Posting details from Neo4j (skills, description)

POST /api/extract-skills
  In:  {text: str}
  Out: {required_skills: List[str], desired_skills: List[str]}
  # Dual-LLM: Claude (claude-4-5-sonnet-latest) for reasoning → gpt-oss-120b for json_schema extraction
  # Claude returns HTTP 500 on response_format json_schema — use GPT for structured output only
```

**Neo4j connection:** `neo4j` Python driver, env vars `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

### Phase 6: Next.js Frontend

**Pages:**
- `/` — Search page: toggle between "Req Number" and "Role Description" input
- `/results` — Candidate ranking results

**Components:**
- `SearchForm`: two-tab input (req number | description + skills)
- `SkillEditor`: chip-based required/desired skill editor (auto-populated, editable)
- `CandidateTable`: ranked list with sortable columns; expand row for evidence
- `ScoreBreakdown`: horizontal bar showing skill/role/experience sub-scores

**API integration:** `fetch` calls to FastAPI backend (configured via `NEXT_PUBLIC_API_URL`)

---

## Environment Setup

**`.env.example`:**
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password12345

# Genesis API (primary LLM backend) — set via: setx GENESIS_SKLZ_API_KEY <token>
# DO NOT put the real key in .env — use system env vars only
GENESIS_SKLZ_API_KEY=your-sklz-org-token-here
GENESIS_BASE_URL=https://api.ai.us.lmco.com/v1
GENESIS_ORG=SKLZ
GENESIS_REASONING_MODEL=claude-4-5-sonnet-latest
GENESIS_EXTRACTION_MODEL=gpt-oss-120b
GENESIS_EMBEDDING_MODEL=mxbai-embed-large-v1

# Bedrock (fallback only — not primary)
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v2:0

SSL_CERT_FILE=C:/Users/e477258/combined_pem.pem
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**`docker-compose.yml`:** Simplified to Neo4j-only (Spark, MinIO, Iceberg removed for prototype speed).

---

## Dependency List

**Python (`pyproject.toml`):**
- `neo4j>=5.0`
- `fastapi`, `uvicorn`
- `openai` (Genesis SDK — OpenAI-compatible)
- `langchain-openai` (LangChain integration for Genesis)
- `httpx` (O*NET + USAJOBS API calls, SSL-aware client for Genesis)
- `duckdb`, `pandas`, `pyarrow`
- `faker`
- `numpy` (cosine similarity)
- `python-dotenv`
- ~~`boto3`~~ (removed — Bedrock not primary)

**Node (`frontend/package.json`):**
- `next`, `react`, `react-dom`
- `@tanstack/react-table` (sortable results table)
- `recharts` (score breakdown chart)
- `tailwindcss`

---

## Verification

After each phase, run the smoke test:
```bash
python scripts/06_smoke_test.py --query "Chief of Staff" --top-k 10
```
Expected output: 10 ranked candidates with composite + pillar scores and evidence text.

End-to-end: start Next.js dev server, enter "Chief of Staff" in search, verify ranked results appear with skill chips and evidence expansion.

---

## Build Order (Parallelizable at Phase 4+)

1. Phase 1 → Phase 2 → Phase 3 (sequential: each feeds the next)
2. Phase 4 + Phase 5 can be built together (scoring engine + API layer)
3. Phase 6 (frontend) can start scaffolding in parallel with Phase 4/5 using mock data
