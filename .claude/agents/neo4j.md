---
name: neo4j
description: Read-only Neo4j schema expert. Load this agent when writing or reviewing Cypher queries, exploring the graph schema, or debugging retrieval logic. Knows all node labels, properties, relationship types, vector indexes, and critical query constraints.
---

# Neo4j Graph Schema Agent

Read-only. Use this agent to write correct Cypher, understand the schema, and avoid known pitfalls.

---

## Connection

- **Bolt URI**: `bolt://localhost:7687`
- **HTTP**: `http://localhost:7474`
- **Credentials**: `neo4j` / `password12345`
- **Vagrant VM**: must be running (`vagrant up` from project root)

---

## Data Counts (current dataset, generated 2026-03-05)

| Entity | Count |
|--------|-------|
| Person | 500 |
| Role | 1267 |
| Skill | 40 |
| Chunk | 1498 |
| Posting | 10 (REQ-001 … REQ-010) |

---

## Node Labels and Properties

### Person
| Property | Type | Notes |
|----------|------|-------|
| `stable_id` | string | Primary key — UUID, used in all joins |
| `name` | string | Full name (synthetic) |
| `current_title` | string | Most recent job title |

### Role
| Property | Type | Notes |
|----------|------|-------|
| `stable_id` | string | UUID |
| `title` | string | Job title |
| `company` | string | Employer name |
| `start_date` | string | ISO 8601 date |
| `end_date` | string | ISO 8601 date or null if current |
| `is_current` | boolean | True if this is the active role |
| `embedding` | float[] | 1024-dim title embedding (mxbai-embed-large-v1) |

### Skill
| Property | Type | Notes |
|----------|------|-------|
| `stable_id` | string | UUID |
| `name` | string | Canonical skill name (e.g., "Python", "Machine Learning") |

### Chunk
| Property | Type | Notes |
|----------|------|-------|
| `stable_id` | string | UUID |
| `text` | string | Resume/experience text fragment |
| `embedding` | float[] | 1024-dim text embedding (mxbai-embed-large-v1) |

### Posting
| Property | Type | Notes |
|----------|------|-------|
| `stable_id` | string | UUID |
| `req_number` | string | Human-readable ID (REQ-001 … REQ-010) |
| `title` | string | Job title |
| `description` | string | Full job description text |

---

## Relationship Types

| Relationship | From → To | Properties | Notes |
|---|---|---|---|
| `HAS_ROLE` | Person → Role | — | All roles, past and current |
| `HAS_SKILL` | Person → Skill | — | Extracted skill tags |
| `HAS_CHUNK` | Person → Chunk | — | Resume text chunks |
| `REQUIRES_SKILL` | Posting → Skill | `required: boolean` | `required=true` = required; `false` = desired |
| `MENTIONS` | Chunk → Skill | — | Skill entity links found in chunk text |

---

## Vector Indexes

| Index Name | Node Label | Property | Dimensions | Similarity |
|---|---|---|---|---|
| `chunk_embedding_idx` | Chunk | `embedding` | 1024 | cosine |
| `role_title_idx` | Role | `embedding` | 1024 | cosine |
| `skill_name_ft` | Skill | `name` | — | fulltext (BM25) |

---

## Critical Cypher Constraints

### WHERE must follow YIELD in vector queries

**Wrong** (pre-filtering — fails):
```cypher
CALL db.index.vector.queryNodes($idx, $top_k, $embedding)
WHERE p.stable_id IN $candidate_ids   -- ERROR: cannot filter before YIELD
YIELD node AS chunk, score
```

**Correct** (post-YIELD filtering):
```cypher
CALL db.index.vector.queryNodes($idx, $top_k, $embedding)
YIELD node AS chunk, score
MATCH (p:Person)-[:HAS_CHUNK]->(chunk)
WHERE p.stable_id IN $candidate_ids   -- OK: filter after YIELD + MATCH
```

### stable_id is the join key — not the internal Neo4j ID

Always join on `p.stable_id`, never on `id(p)` or `elementId(p)`.

### REQUIRES_SKILL required flag scoring

`r.required = true` → weight 2 (required skill match)
`r.required = false` → weight 1 (desired skill match)

---

## Cypher Query Constants (from `src/graph/queries.py`)

### POSTING_GRAPH_SEED
Graph-seed: returns candidates ranked by skill overlap with a posting.
Required skills score 2, desired skills score 1.

```cypher
MATCH (po:Posting)-[r:REQUIRES_SKILL]->(s:Skill)<-[:HAS_SKILL]-(p:Person)
WHERE po.req_number = $req_number
WITH p.stable_id AS person_id,
     collect(DISTINCT s.name) AS matched_skill_names,
     sum(CASE WHEN r.required THEN 2 ELSE 1 END) AS raw_score
RETURN person_id, matched_skill_names, raw_score
ORDER BY raw_score DESC
```

### SKILL_LIST_GRAPH_SEED
Fallback seed when no req_number is available — matches by raw skill list.

```cypher
MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
WHERE toLower(s.name) IN $skill_names_lower
WITH p.stable_id AS person_id,
     collect(DISTINCT s.name) AS matched_skill_names,
     count(DISTINCT s) AS match_count
RETURN person_id, matched_skill_names, match_count
ORDER BY match_count DESC
```

### CHUNK_VECTOR_FILTERED
Filtered chunk vector re-rank — constrained to a seeded candidate pool.
`WHERE` after `YIELD` is required. Includes MENTIONS expansion.

```cypher
CALL db.index.vector.queryNodes($idx, $top_k, $embedding)
YIELD node AS chunk, score
MATCH (p:Person)-[:HAS_CHUNK]->(chunk)
WHERE p.stable_id IN $candidate_ids
OPTIONAL MATCH (chunk)-[:MENTIONS]->(s:Skill)
WITH p.stable_id AS person_id, chunk, score, collect(s.name) AS mentioned_skills
RETURN person_id, avg(score) AS avg_chunk_score,
       collect(mentioned_skills) AS all_mentioned_skill_lists
ORDER BY avg_chunk_score DESC
```

### ROLE_VECTOR_FILTERED
Filtered role title vector re-rank — constrained to candidate pool.

```cypher
CALL db.index.vector.queryNodes($idx, $top_k, $embedding)
YIELD node AS role, score
MATCH (p:Person)-[:HAS_ROLE]->(role)
WHERE p.stable_id IN $candidate_ids
RETURN p.stable_id AS person_id, role.is_current AS is_current,
       role.start_date AS start_date, score
ORDER BY person_id, is_current DESC, start_date DESC
```

### POSTING_REQUIRED_SKILLS
Get all skills (required + desired) for a posting.

```cypher
MATCH (po:Posting)-[r:REQUIRES_SKILL]->(s:Skill)
WHERE po.req_number = $req_number
RETURN s.name AS skill_name, r.required AS required
```

### PERSON_SKILLS
Bulk-fetch all skills for a list of persons.

```cypher
MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
WHERE p.stable_id IN $ids
RETURN p.stable_id AS person_id, collect(s.name) AS skills
```

### PERSON_BY_IDS
Fetch name + current title for a list of persons.

```cypher
MATCH (p:Person)
WHERE p.stable_id IN $ids
RETURN p.stable_id AS id, p.name AS name, p.current_title AS current_title
```

### PERSON_CHUNK_EVIDENCE
Best chunks per candidate for LLM evidence generation.

```cypher
CALL db.index.vector.queryNodes($idx, $top_k, $embedding)
YIELD node AS chunk, score
MATCH (p:Person)-[:HAS_CHUNK]->(chunk)
WHERE p.stable_id IN $ids
RETURN p.stable_id AS person_id, chunk.text AS text, score
ORDER BY score DESC
```

---

## Graph RAG Retrieval Pipeline (HybridRetriever)

The two-stage retrieval in `src/graph/hybrid_retriever.py`:

1. **Graph seed** — `POSTING_GRAPH_SEED` → set of `candidate_ids` (persons with matching skills)
2. **Filtered vector re-rank** — `CHUNK_VECTOR_FILTERED` + `ROLE_VECTOR_FILTERED` constrained to `candidate_ids`
3. **LLM evidence** — single batched Claude call with `CANDIDATE N:` plain-text markers (never `json_schema` — returns HTTP 500 on Claude)

Three-pillar composite score: skill match + role history + chunk similarity.
