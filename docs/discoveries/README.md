# Hackathon Discovery Documents

> **Investigation Date**: March 5, 2026  
> **Purpose**: Capture what was investigated, how it was verified, and what is currently actionable.

These documents summarize hands-on investigation of this codebase and surrounding infrastructure. The focus is command-backed findings, not assumptions.

---

## Documents

### [01 - Environment and Connections](./01-environment-and-connections.md)
Service inventory, connection endpoints, discovered credentials, and environment constraints.

**Key finding**: Neo4j at `bolt://140.169.17.180:7687` (from `model-api/rest.env`) was reachable during investigation.

---

### [02 - SKLZ Neo4j Schema](./02-sklz-neo4j-schema.md)
Schema inspection for the real SKLZ graph database, including core labels and relationship families.

**Key finding**: Production SKLZ graph contains large-scale `Employee`, `Skill`, and `JobReq` data, but no native vector index path in the inspected runtime generation.

---

### [03 - Codebase Architecture](./03-codebase-architecture.md)
Map of backend/frontend/pipeline structure, plus runtime assumptions and observed gaps at that time.

**Key finding**: Core routing and synthetic data generation worked, but the original Docker-only import assumption blocked full local bootstrap on the work machine.

---

### [04 - Synthetic vs Real Data Gap](./04-synthetic-vs-real-data-gap.md)
Direct mapping of synthetic labels/relationships to real SKLZ schema equivalents and incompatibilities.

**Key finding**: Prototype graph model (`Person/Role/Chunk/Posting`) does not map 1:1 to the real SKLZ graph model (`Employee/JobReq/OpenReq`), so adapters or query rewrites are required.

---

### [05 - Hackathon Strategy Options](./05-hackathon-strategy-options.md)
Phased implementation options with tradeoffs, timelines, and recommended execution order.

**Key finding**: A phased plan (real-data compatibility first, embedding/vector enhancements second) was the lowest-risk path.

---

### [06 - Local Vagrant Neo4j Runtime Validation](./06-local-vagrant-runtime-validation.md)
Validated local runtime for fresh graph creation using Vagrant + VirtualBox with Neo4j 5.26.21.

**Key finding**: `vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"` rebuilt the `neo4j` database successfully with `3315` nodes and `8558` relationships, with host connectivity verified on `localhost:7474` and `localhost:7687`.

---

### [07 - Frontend Corporate Style and Playwright E2E](./07-frontend-corporate-style-playwright-e2e.md)
Captured the finalized frontend design refresh and committed deterministic Playwright e2e workflow.

**Key finding**: `npm.cmd run test:e2e` now provides repeatable frontend regression coverage (3 passing specs) using mocked API routes, independent of backend uptime.

---

## Quick Reference: Critical Credentials

| Service | Address | User | Password |
|---------|---------|------|----------|
| Neo4j SKLZ main | `bolt://140.169.17.180:7687` | `neo4j` | `graph_admin` |
| Neo4j Attrition | `bolt://140.169.17.208:7687` | `neo4j` | `hca_graph` |
| PostgreSQL (via Vagrant) | `localhost:5432` | `hcaprd` | `hca_admin` |
| Neo4j 5.x (hackathon target?) | `140.169.17.216:7474` | `neo4j` | Unknown |

---

## Quick Reference: Real SKLZ Node Counts

| Node Label | Count | Notes |
|------------|-------|-------|
| `Employee` | 122,893 | Real LMCO employees |
| `Skill` | 217,513 | Skill taxonomy and evidence graph |
| `JobReq` | 190,747 | Historical requisitions |
| `OpenReq` | TBD | Active/open positions |
| **Total** | **897,381** | All nodes (snapshot from discovery) |

---

## Quick Reference: Schema Mapping (Synthetic -> Real)

| Synthetic Label | Real SKLZ Label | Fix |
|----------------|----------------|-----|
| `Person` | `Employee` | Rename/query rewrite |
| `Role` | `Job` or `JobTitle` | Rename/query rewrite |
| `Chunk` | N/A | Remove or replace with evidence pattern |
| `Posting` | `OpenReq` | Rename/query rewrite |
| `p.stable_id` | `e.emplid` | Property mapping update |
| `[:HAS_SKILL]` | `[:EVIDENCE_FOR]` | Relationship mapping update |
| `[:HAS_ROLE]` | Unknown | Requires graph inspection |
| `po.req_number` | `jr.req_num` | Property mapping update |

---

## Next Investigation Steps

Use these query prompts to close remaining schema gaps in external SKLZ graphs:

```python
# Q1: What outgoing relationship types exist from Employee?
"MATCH (e:Employee)-[r]->() RETURN DISTINCT type(r) AS rel_type"

# Q2: How are OpenReq skills represented?
"MATCH (jr:OpenReq) WHERE jr.required_skills IS NOT NULL RETURN jr.req_num, jr.required_skills LIMIT 3"

# Q3: How many OpenReq nodes exist?
"MATCH (jr:OpenReq) RETURN count(jr) AS cnt"

# Q4: What relationship type connects OpenReq/JobReq to Skill?
"MATCH (jr:OpenReq)-[r]->(s:Skill) RETURN DISTINCT type(r) LIMIT 1"
"MATCH (jr:JobReq)-[r]->(s:Skill) RETURN DISTINCT type(r) LIMIT 1"

# Q5: Is there a SkillRecommendation -> Employee relationship?
"MATCH (sr:SkillRecommendation)-[r]->(e:Employee) RETURN DISTINCT type(r) LIMIT 1"
```
