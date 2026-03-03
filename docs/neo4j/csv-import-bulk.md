# Neo4j Bulk CSV Import

## Goal
Load first-time graph stores quickly with `neo4j-admin database import full`.

## Preconditions
- Neo4j container is stopped for import.
- Node/edge CSV files and matching header files are prepared.
- IDs are deterministic and consistent across node/relationship files.

## Header Pattern
Node header example (`person_header.csv`):
```csv
personId:ID(Person),fullName:string,source_system:string,source_id:string,stable_id:string,:LABEL
```

Relationship header example (`has_skill_header.csv`):
```csv
:START_ID(Person),:END_ID(Skill),confidence:float,extractor_version:string,:TYPE
```

## Import Command
```bash
docker compose stop neo4j

docker run --rm \
  --network prototype-pipeline_pipeline_net \
  -v neo4j_data:/data \
  -v neo4j_import:/import \
  neo4j:2026.01.4-community-ubi10 \
  neo4j-admin database import full \
  --overwrite-destination=true \
  --delimiter=, \
  --array-delimiter=';' \
  --quote='"' \
  --skip-bad-relationships=false \
  --nodes=Person=/import/person_header.csv,/import/person.csv \
  --nodes=Role=/import/role_header.csv,/import/role.csv \
  --nodes=Skill=/import/skill_header.csv,/import/skill.csv \
  --nodes=Posting=/import/posting_header.csv,/import/posting.csv \
  --nodes=Chunk=/import/chunk_header.csv,/import/chunk.csv \
  --relationships=HAS_ROLE=/import/has_role_header.csv,/import/has_role.csv \
  --relationships=REQUIRES_SKILL=/import/requires_skill_header.csv,/import/requires_skill.csv \
  --relationships=MENTIONS=/import/mentions_header.csv,/import/mentions.csv \
  --relationships=DERIVED_FROM=/import/derived_from_header.csv,/import/derived_from.csv \
  neo4j

docker compose start neo4j
```

## Post-Import Schema
```cypher
CREATE CONSTRAINT person_stable_id IF NOT EXISTS
FOR (p:Person) REQUIRE p.stable_id IS UNIQUE;

CREATE CONSTRAINT skill_stable_id IF NOT EXISTS
FOR (s:Skill) REQUIRE s.stable_id IS UNIQUE;

CREATE CONSTRAINT posting_stable_id IF NOT EXISTS
FOR (j:Posting) REQUIRE j.stable_id IS UNIQUE;

CREATE INDEX posting_title IF NOT EXISTS
FOR (j:Posting) ON (j.title);
```

## Verification Queries
```cypher
MATCH (n:Person) RETURN count(n) AS persons;
MATCH (n:Skill) RETURN count(n) AS skills;
MATCH ()-[r:REQUIRES_SKILL]->() RETURN count(r) AS rels;
```

## Official References
- https://neo4j.com/docs/operations-manual/current/tutorial/neo4j-admin-import/
- https://neo4j.com/docs/operations-manual/current/import/
- Accessed: 2026-03-03
- Version: Neo4j 2026.01 docs branch
