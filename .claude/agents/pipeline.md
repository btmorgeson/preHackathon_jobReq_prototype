---
name: pipeline
description: Data pipeline orchestration expert. Load this agent when running, debugging, or reasoning about the 5-step ingestion pipeline. Knows exact commands, step ordering, what each step produces, idempotency, and how to resume from partial runs.
---

# Pipeline Orchestration Agent

This agent covers the one-time data pipeline that populates Neo4j from scratch.
Do not use for live API or frontend work — see `src/api/` and `frontend/` instead.

---

## Pipeline Overview

```
O*NET fetch → synthetic employees → graph CSVs → Neo4j import → embeddings + indexes
   step 1          step 2             step 3          step 4           step 5
```

Steps must run in order. Step 4 runs **inside the Vagrant VM**, not on the host.

---

## Environment Prerequisites

```bash
# Required for every step
export PYTHONPATH=.

# Required for step 5 only (Genesis embedding API)
export GENESIS_SKLZ_API_KEY="$(powershell.exe -Command "[System.Environment]::GetEnvironmentVariable('GENESIS_SKLZ_API_KEY','User')" | tr -d '\r')"

# Confirm the key loaded
echo "Key length: ${#GENESIS_SKLZ_API_KEY}"  # should be > 0
```

---

## Step-by-Step Reference

### Step 1 — Fetch O*NET data
```bash
PYTHONPATH=. python scripts/01_fetch_onet.py
```
**Produces**: `data/onet/` — SOC code taxonomy (occupation titles, task descriptions)
**Idempotent**: Yes — re-running overwrites safely
**Known issue**: O*NET zip download fails on corporate network (IncompleteRead). Script uses a hardcoded fallback dataset (35 SOC codes). No action needed if download fails — fallback activates automatically.

---

### Step 2 — Generate synthetic employees
```bash
PYTHONPATH=. python scripts/02_generate_employees.py
```
**Produces**: `data/employees.parquet` — 500 synthetic persons with roles, skills, and experience chunks
**Idempotent**: Yes — deterministic seed
**Dependencies**: Step 1 output (`data/onet/`)
**Data**: 500 persons, 1267 roles, 40 skills, 1498 chunks, 10 postings (REQ-001..REQ-010)

---

### Step 3 — Build graph CSVs
```bash
PYTHONPATH=. python scripts/03_build_graph_csv.py
```
**Produces**: `data/graph_csv/` — Neo4j bulk-import CSV files (nodes + relationships)
**Idempotent**: Yes
**Dependencies**: Step 2 output (`data/employees.parquet`)
**Critical**: `:ID` column is NOT stored as a node property. `stable_id` is a separate column — always present in node CSVs and used as the join key in all relationship CSVs.

---

### Step 4 — Import into Neo4j (Vagrant VM)
```bash
vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"
```
**Runs inside**: Vagrant VM (Ubuntu 22.04, Neo4j 5.26.21)
**Produces**: Populated Neo4j database with all nodes and relationships
**Idempotent**: Yes — `reset_and_import.sh` drops and recreates the database
**VM must be running**: `vagrant up` from project root
**What `reset_and_import.sh` does**:
  1. Stops Neo4j service
  2. Drops existing database
  3. Runs `neo4j-admin database import full` from `/workspace/data/graph_csv/`
  4. Restarts Neo4j service
  5. Applies schema constraints and indexes

**Note**: `scripts/04_neo4j_import.py` is an alternate Docker-based path — NOT used on this machine (Vagrant is the standard path).

---

### Step 5 — Generate embeddings and build vector indexes
```bash
PYTHONPATH=. python scripts/05_embed_chunks.py
```
**Produces**: 1024-dim embeddings written to `Chunk.embedding` and `Role.embedding` properties; vector indexes `chunk_embedding_idx` and `role_title_idx`; MENTIONS relationships (Chunk → Skill)
**Idempotent**: Partially — reruns embed all nodes again (expensive). Use `--rebuild-mentions` to only rerun the entity linker.
**Dependencies**: Step 4 (Neo4j must have nodes), `GENESIS_SKLZ_API_KEY` must be set
**Estimated runtime**: ~5-10 minutes for 500 persons × chunks + roles
**Embedding model**: `mxbai-embed-large-v1` (1024 dims, cosine similarity) via Genesis API

```bash
# Rerun only the MENTIONS entity linker (fast — no embedding API calls)
PYTHONPATH=. python scripts/05_embed_chunks.py --rebuild-mentions
```

---

## Full Orchestration (with quality gates)

```bash
PYTHONPATH=. python scripts/run_pipeline.py
```

Runs all 5 steps in sequence with pre/post validation gates. Use this for a clean full rebuild.

---

## Resuming from a Partial Run

| Symptom | Resume from |
|---|---|
| `data/onet/` missing | Step 1 |
| `data/employees.parquet` missing | Step 2 |
| `data/graph_csv/` empty or missing | Step 3 |
| Neo4j has 0 nodes (`MATCH (n) RETURN count(n)`) | Step 4 |
| Nodes exist but `chunk.embedding` is null | Step 5 |
| `MENTIONS` relationships missing | Step 5 with `--rebuild-mentions` |

**Check Neo4j state** (from host, Vagrant VM must be running):
```bash
# Quick node count
cypher-shell -u neo4j -p password12345 "MATCH (n) RETURN labels(n), count(*) AS cnt ORDER BY cnt DESC"
```

---

## Smoke Tests

After a full pipeline run, validate end-to-end with:
```bash
PYTHONPATH=. python scripts/06_smoke_test.py
```

Runs 7 API smoke tests against the live FastAPI server (must be running on port 8000).
**Expected**: 7/7 pass.

---

## Key File Locations

| File | Purpose |
|------|---------|
| `scripts/01_fetch_onet.py` | O*NET taxonomy fetch |
| `scripts/02_generate_employees.py` | Synthetic employee generation (Faker) |
| `scripts/03_build_graph_csv.py` | Graph CSV builder |
| `scripts/vagrant/reset_and_import.sh` | VM-side DB reset + neo4j-admin import |
| `scripts/05_embed_chunks.py` | Genesis embedding pipeline + entity linker |
| `scripts/run_pipeline.py` | Full orchestration with quality gates |
| `scripts/06_smoke_test.py` | End-to-end API validation (7 tests) |
| `data/graph_csv/` | Neo4j bulk-import CSVs (do not hand-edit) |
| `src/pipeline/embed/embed_pipeline.py` | Embedding logic + `link_chunk_mentions()` |
| `src/pipeline/load/graph_csv_builder.py` | CSV builder logic |
