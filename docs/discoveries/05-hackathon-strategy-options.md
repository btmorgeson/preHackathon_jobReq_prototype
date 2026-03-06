# Discovery 05: Hackathon Strategy Options

> **Date**: March 5, 2026  
> **Author**: Cline AI (investigation session)  
> **Purpose**: Present concrete implementation paths for the hackathon, with trade-offs clearly stated

---

## The Decision Matrix

We have discovered we're not limited to the old SKLZ graph DB. The user explicitly said:
> "the hackathon is not limited to the current sklz graph database so i don't want to handicap ourselves yet"

This opens up the full design space. Here are the viable paths:

---

## Option A: Adapt to Real SKLZ Data (.180) — No Vector Search

**Summary**: Use the real 122k employee / 190k job req database with text-based matching. Sacrifice semantic search for real data depth.

### What Changes
- Rewrite all queries to use `Employee`, `OpenReq`, `EVIDENCE_FOR` schema
- Replace vector search pillars with property-based scoring:
  - **Experience pillar** → `service_years` + `job_level` normalized score
  - **Role History pillar** → skill cluster matching (indirect role signal)
  - **Skill pillar** → `EVIDENCE_FOR` exact match (works fine)
- Candidate pool seeded by skill match, not vector similarity

### Scoring Strategy (No Vector)
```
Skill Pillar (0.4):     Count matched skills / total required skills
Experience Pillar (0.3): Normalized(service_years) + job_level_bonus
Role History (0.3):     Skill cluster overlap with job req skill clusters
                        + time_in_grade as current role depth proxy
```

### Pros
- ✅ **Real data** — 122k actual LMCO employees (incredibly impressive for demo)
- ✅ Connected immediately — Neo4j at `.180` already working
- ✅ No data import needed
- ✅ Fastest path to working demo
- ✅ `OpenReq` has real job postings to browse and search

### Cons
- ❌ No semantic understanding — "machine learning" ≠ "ML" ≠ "deep learning"
- ❌ Experience pillar is shallow (just `service_years` + `job_level`)
- ❌ Role history pillar loses career trajectory semantic matching
- ❌ Must navigate read-only constraints (we don't own this database)

### Estimated Implementation Time: 4-6 hours

---

## Option B: Neo4j 5.x Instance (.216) with Full Vector Search

**Summary**: Get credentials for the Neo4j 5.26.0 instance at `.216`, import synthetic or augmented real data with embeddings, run the original vector-based architecture.

### What's Needed
1. Credentials for `140.169.17.216` (ask Rob/Ethan/Mac)
2. Import our synthetic data OR a subset of real SKLZ data (anonymized)
3. Run `scripts/05_embed_chunks.py` to generate embeddings via Genesis
4. Create vector indexes:
   ```cypher
   CREATE VECTOR INDEX chunk_embedding_idx FOR (c:Chunk) ON (c.embedding)
   OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}
   
   CREATE VECTOR INDEX role_title_idx FOR (r:Role) ON (r.embedding)
   OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}
   ```
5. Run original pipeline (modified to import via Cypher instead of `docker cp`)

### Pros
- ✅ **Full semantic search** — the original architecture as designed
- ✅ Vector similarity finds candidates with related-but-not-exact-match skills
- ✅ Role history pillar works as designed with recency decay
- ✅ Can showcase Genesis AI embeddings meaningfully
- ✅ Clean slate — we control the schema entirely
- ✅ 500 synthetic employees still gives a solid demo

### Cons
- ❌ Credentials unknown — blocks everything until resolved
- ❌ Synthetic data (500 employees) less impressive than 122k real employees
- ❌ Need to run embedding pipeline (time + Genesis API key required)
- ❌ Must fix docker-less import (rewrite script 04 to use Cypher)

### Estimated Implementation Time: 8-12 hours (plus credential resolution)

---

## Option C: Hybrid — Real SKLZ Data + Genesis Embeddings On-The-Fly

**Summary**: Query real SKLZ data from `.180`, but compute semantic similarity at query time using Genesis AI embeddings rather than storing them in Neo4j.

### Architecture
```
SearchRequest
    │
    ▼
Genesis AI: Embed query text → 1024-dim vector
    │
    ├──► Skill Pillar: SKLZ .180 exact match (EVIDENCE_FOR)
    │
    ├──► Experience Pillar: SKLZ .180 property scoring (service_years, job_level)
    │
    └──► Role History: SKLZ .180 + Genesis similarity comparison
         └── Get candidate Job titles from SKLZ
         └── Compute cosine_similarity(query_embedding, title_embedding) in Python
         └── No vector index needed — compute at query time
    
    ▼
Combine, rank, return top_k
```

### How It Works (Runtime Embedding)
```python
# Instead of vector index in Neo4j, embed and compare in Python:
import numpy as np

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Get all candidate job titles from SKLZ
candidates = session.run(
    "MATCH (e:Employee)-[:EVIDENCE_FOR]->(s:Skill) "
    "WHERE s.name IN $required_skills "
    "WITH e LIMIT 500 "
    "MATCH (e)-[:HOLDS_TITLE]->(jt:JobTitle) "
    "RETURN e.emplid, e.full_name, jt.title"
).data()

# Embed all candidate titles in a batch
titles = [c['title'] for c in candidates]
title_embeddings = embed_batch(client, titles)  # Genesis API call

# Score similarity to query
query_emb = embed_batch(client, [query_text])[0]
for c, emb in zip(candidates, title_embeddings):
    c['role_score'] = cosine_sim(query_emb, emb)
```

### Pros
- ✅ Real SKLZ data (122k employees)
- ✅ Semantic similarity via Genesis embeddings
- ✅ No vector index required in Neo4j
- ✅ Most sophisticated demo — real data + AI semantics
- ✅ No credential problem — `.180` already works

### Cons
- ❌ Slower (Genesis API calls per search request)
- ❌ Rate limits on Genesis embedding API
- ❌ Only works for candidates pre-filtered by skill match (can't embed all 122k employees)
- ❌ Need Genesis API key (`GENESIS_SKLZ_API_KEY` env var)

### Estimated Implementation Time: 6-8 hours

---

## Option D: Full Architecture on Neo4j 5.x + Real SKLZ Data Subset

**Summary**: Export a sanitized subset of real SKLZ data (e.g., 5k employees + their skills + job history), import into `.216`, add text chunks derived from job descriptions, run full embedding pipeline, get both real data AND vector search.

### Process
1. Export from SKLZ .180:
   ```cypher
   MATCH (e:Employee)-[:EVIDENCE_FOR]->(s:Skill)
   WITH e, collect(s.name) as skills
   RETURN e.emplid, e.full_name, e.job_level, e.service_years, skills
   LIMIT 5000
   ```
2. Transform to our `Person` schema format
3. Generate text chunks from SKLZ OpenReq descriptions (already have text!)
4. Import to `.216` Neo4j 5.x
5. Run embedding pipeline on chunks
6. Create vector indexes

### Pros
- ✅ Real data + full vector architecture
- ✅ Best of both worlds
- ✅ Most "production-like" demo

### Cons
- ❌ Most complex implementation
- ❌ Still need `.216` credentials
- ❌ Data transformation overhead

### Estimated Implementation Time: 12-16 hours

---

## Recommendation: Start with Option A, Upgrade to C or B

### Phase 1 (Do Now — 4-6 hours)
Implement **Option A** to get a working end-to-end demo:
1. Rewrite queries for real SKLZ schema
2. Adapt scoring pillars to property-based (no vectors)
3. Start API and frontend
4. Demo works with real 122k employee data

### Phase 2 (If Genesis Key Available — Option C)
Add semantic search on top of real data:
1. Embed query text via Genesis
2. Compute cosine similarity at runtime for skill cluster + role matching
3. Demo now has both real data AND AI semantics

### Phase 3 (If .216 Credentials Available — Option B/D)
Build the full vector-indexed architecture:
1. Get .216 credentials
2. Import data subset (real or synthetic)
3. Run embedding pipeline
4. Enable full `db.index.vector.queryNodes()` searches

---

## Immediate Next Steps (Before Choosing)

### Must-Knows (Get ASAP)
1. **Does anyone have a Genesis API key?** → Determines if we can do semantic embeddings
2. **Who has .216 credentials?** → Determines if we can use full vector architecture
3. **Can we write to .180?** → Determines if we can add vector indexes to real data
4. **What is the `.216` instance for?** → May already have data + indexes set up for hackathon

### Quick Wins (Can Do Now)
1. Set env vars: `NEO4J_URI=bolt://140.169.17.180:7687`, `NEO4J_USER=neo4j`, `NEO4J_PASSWORD=graph_admin`
2. Sample real OpenReq data to understand skill format (list vs string vs JSON)
3. Test a basic skill-match query against real SKLZ data
4. Start the FastAPI backend (will fail on first search but proves startup works)
5. Start the Next.js frontend and verify UI renders

### Key Queries to Run Now

```python
# 1. How are required_skills stored in OpenReq?
records = session.run(
    "MATCH (jr:OpenReq) WHERE jr.required_skills IS NOT NULL "
    "RETURN jr.req_num, jr.required_skills, jr.title LIMIT 3"
).data()
print(records)

# 2. What relationships does Employee have?
records = session.run(
    "MATCH (e:Employee)-[r]->() RETURN DISTINCT type(r) as rel_type"
).data()
print([r['rel_type'] for r in records])

# 3. How many OpenReqs are there?
count = session.run("MATCH (jr:OpenReq) RETURN count(jr) as cnt").single()['cnt']
print(f"OpenReqs: {count}")

# 4. Sample employees with many skills
records = session.run(
    "MATCH (e:Employee)-[:EVIDENCE_FOR]->(s:Skill) "
    "RETURN e.emplid, e.full_name, count(s) as skill_count "
    "ORDER BY skill_count DESC LIMIT 10"
).data()
```

---

## The Hackathon Value Proposition

Regardless of which option we choose, the demo story is:

> **"We built an AI-powered job req → candidate ranking system that leverages the SKLZ graph database to surface the best internal talent for any open position — in seconds."**

Key talking points:
- **Real data**: 122k+ LMCO employees with verified skill evidence
- **Three-pillar AI scoring**: Skills match + Career trajectory + Experience depth
- **Explainable AI**: Every score broken down so hiring managers can understand why
- **Adjustable weights**: Different roles can weight skills vs. experience differently
- **Live job postings**: Search from real open reqs or type any job description

The most impactful line for the demo:
> "Instead of a recruiter spending hours combing through resumes, our system analyzes the entire LMCO workforce and gives you a ranked, explainable list in under 2 seconds."
