# Neo4j Layer

## Purpose
Define how graph data is bulk loaded, constrained, indexed, and queried for the prototype pipeline.

## What You'll Learn
- How to run Neo4j locally with Docker.
- How to bulk-import graph CSV files with `neo4j-admin`.
- How to create constraints/indexes, including vector indexes.

## Prerequisites
- `docker compose` running from repo root.
- Exported node/edge CSV files and headers.
- Neo4j credentials (`neo4j/password12345` in local compose by default).

## Quickstart
1. Start services: `docker compose up -d neo4j`.
2. Validate health: `curl -I http://localhost:7474`.
3. Follow bulk import guide: [`csv-import-bulk.md`](csv-import-bulk.md).
4. Apply constraints/indexes and run validation queries from [`cypher-patterns.md`](cypher-patterns.md).

## Deep Dive
- Setup and operations: [`local-setup-docker.md`](local-setup-docker.md)
- Import mechanics: [`csv-import-bulk.md`](csv-import-bulk.md)
- Query templates: [`cypher-patterns.md`](cypher-patterns.md)
- Pitfalls: [`gotchas.md`](gotchas.md)
- Source catalog: [`official-sources.md`](official-sources.md)

## Common Mistakes / Gotchas
- Running `neo4j-admin database import full` while DBMS is online.
- Importing mixed-type IDs across files.
- Forgetting uniqueness constraints before app writes begin.

## Official Sources
- Neo4j Docker introduction: https://neo4j.com/docs/operations-manual/current/docker/introduction/ (Accessed: 2026-03-03, Version: Neo4j 2026.01 docs branch)
- Neo4j admin import tutorial: https://neo4j.com/docs/operations-manual/current/tutorial/neo4j-admin-import/ (Accessed: 2026-03-03, Version: Neo4j 2026.01 docs branch)
- Neo4j constraints: https://neo4j.com/docs/cypher-manual/current/constraints/managing-constraints/ (Accessed: 2026-03-03, Version: Cypher Manual current)
- Neo4j vector indexes: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/ (Accessed: 2026-03-03, Version: Cypher Manual current)
