# Tech Context

## Project
Pre-hackathon prototype: Job Req -> Candidate Ranking (LMCO HR AI Hackathon, March 23-26 2026)
Repo: `C:/Users/%USERNAME%/Documents/dev/preHackathon_jobReq_prototype`

## Runtime Baseline (validated 2026-03-05)
- Neo4j runtime: Vagrant VM (Ubuntu 22.04, Neo4j 5.26.21), Docker path remains available as alternate.
- Import command (fresh database):
  - `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"`
- Last verified import totals:
  - `3315` nodes
  - `8558` relationships
- Host connectivity:
  - `http://localhost:7474` (HTTP) -> 200 OK
  - `bolt://localhost:7687` (Bolt) -> connectivity verified with `neo4j/password12345`

## LLM Backend - Genesis API (primary)
| Parameter | Value |
|-----------|-------|
| Base URL | `https://api.ai.us.lmco.com/v1` |
| Org header | `openai-organization: SKLZ` |
| API key env var | `GENESIS_SKLZ_API_KEY` (system env, set via `setx`) |
| SDK | `openai` (OpenAI-compatible) |
| Reasoning model | `claude-4-5-sonnet-latest` |
| Extraction model | `gpt-oss-120b` (structured JSON output) |
| Embedding model | `mxbai-embed-large-v1` (1024 dims, cosine) |
| SSL cert | `C:/Users/%USERNAME%/combined_pem.pem` |
| Bedrock | Fallback only (not primary) |

## Python Dependencies (installed, see pyproject.toml)
```text
neo4j>=5.0
fastapi
uvicorn
openai
httpx
duckdb
pandas
pyarrow
faker
numpy
python-dotenv
```
Note: `langchain-openai` was removed. Direct `openai` SDK usage is the current path.

## Graph Database - Neo4j
- Driver: `neo4j` Python driver (v6.1.0)
- Connection env vars: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- Default host settings: `bolt://localhost:7687`, user `neo4j`, password `password12345`
- Primary deployment: Vagrant VM
  - `vagrant up`
  - `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"`
  - Ports forwarded: 7474 (HTTP), 7687 (Bolt)
  - Project root in VM: `/workspace`
- Alternate deployment: Docker (`scripts/04_neo4j_import.py` path)

## Graph Schema
```text
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

## Vector Indexes (Neo4j)
```cypher
CALL db.index.vector.createNodeIndex('chunk_embedding_idx', 'Chunk', 'embedding', 1024, 'cosine')
CALL db.index.vector.createNodeIndex('role_title_idx', 'Role', 'title_embedding', 1024, 'cosine')
```

## Frontend
- Next.js App Router
- `@tanstack/react-table`, `recharts`, `tailwindcss`
- API URL env: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- UI theme baseline (2026-03-06):
  - tokenized light corporate palette with cyan accents in `frontend/app/globals.css`
  - local corporate font stacks (no `next/font/google` dependency; avoids TLS fetch failures on corporate network)
  - Playwright-validated desktop/mobile interaction flow for req lookup and role-description extraction
- Committed e2e harness (2026-03-06):
  - config: `frontend/playwright.config.ts`
  - specs: `frontend/e2e/app.spec.ts` (mocked API flows for deterministic frontend checks)
  - scripts: `npm.cmd run test:e2e`, `npm.cmd run test:e2e:headed`, `npm.cmd run test:e2e:report`
  - first-time browser install: `npx.cmd playwright install chromium`

## Backend
- FastAPI + uvicorn
- Endpoints:
  - `POST /api/search`
  - `GET /api/postings/{req_number}`
  - `POST /api/extract-skills`

## Data Sources
- O*NET Web Services API
- USAJOBS API (sample postings)
- Synthetic employees generated from Faker + O*NET role/skill data (500-1000 records target)

## Windows Environment
- Shells: PowerShell + Git Bash
- Python command: `python`
- Node: `v22.22.0` at `/c/Program Files/nodejs/node`
- SSL cert path: `C:/Users/%USERNAME%/combined_pem.pem`
- HTTP client TLS: `httpx.Client(verify="C:/Users/%USERNAME%/combined_pem.pem")`
- Python HTTP env vars: `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`

## Running the App (host flow)
All python commands from repo root require `PYTHONPATH=.`.

1. `vagrant up`
2. `python scripts/03_build_graph_csv.py`
3. `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"`
4. `python scripts/05_embed_chunks.py` (requires `GENESIS_SKLZ_API_KEY`)
5. `python -m uvicorn src.api.main:app --reload --port 8000`
6. `python scripts/06_smoke_test.py`

Git Bash note for API key export:
```bash
export GENESIS_SKLZ_API_KEY="$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('GENESIS_SKLZ_API_KEY','User')" | tr -d '\r')"
```

## Key Files
| File | Purpose |
|------|---------|
| `README.md` | Canonical host runbook with Vagrant-first flow |
| `scripts/tasks.ps1` | Operator task runner (`vagrant-up`, `vagrant-reset`, pipeline/API/frontend/smoke) |
| `scripts/vagrant/provision_neo4j.sh` | VM provisioner (Neo4j 5.26.21 + corporate TLS fallback logic) |
| `scripts/vagrant/reset_and_import.sh` | Fresh DB rebuild from graph CSV exports in VM |
| `scripts/04_neo4j_import.py` | Docker-only import path (alternate runtime) |
| `scripts/05_embed_chunks.py` | Embedding pipeline + vector index management |
| `scripts/06_smoke_test.py` | End-to-end API smoke tests |
| `src/pipeline/load/graph_csv_builder.py` | Graph CSV builder; writes explicit `stable_id` properties |
| `src/api/main.py` | FastAPI app entrypoint |
| `src/config.py` | Centralized runtime settings |
| `Vagrantfile` | Disposable Neo4j VM definition |
| `frontend/` | Next.js app |
| `.env.example` | Environment variable template |
