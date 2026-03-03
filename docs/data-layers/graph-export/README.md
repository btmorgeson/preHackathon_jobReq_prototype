# Graph Export Layer

## Purpose
Define node and relationship table outputs that bridge curated data layers and Neo4j bulk import.

## What You'll Learn
- Node/edge table design for this prototype domain.
- Deterministic ID strategy for reproducible imports.
- How to map exports to `neo4j-admin` headers and commands.

## Prerequisites
- Curated parquet or Iceberg tables.
- Canonical ID strategy from datasets/schema notes.

## Quickstart
1. Review node specs: [`node-tables.md`](node-tables.md).
2. Review edge specs: [`edge-tables.md`](edge-tables.md).
3. Export CSVs into `data/exports/graph/`.
4. Apply mapping in [`neo4j-import-mapping.md`](neo4j-import-mapping.md).

## Deep Dive
- IDs and lineage semantics.
- Relationship cardinalities and inferred-edge metadata.
- Cross-layer reconciliation between lake and graph projections.

## Common Mistakes / Gotchas
- Emitting non-deterministic IDs.
- Omitting `source_system` and `source_id` from nodes.
- Failing to version inference outputs.

## Official Sources
- Neo4j import schema rules: https://neo4j.com/docs/operations-manual/current/tutorial/neo4j-admin-import/ (Accessed: 2026-03-03, Version: Neo4j 2026.01 docs branch)
- Neo4j data modeling guidance: https://neo4j.com/docs/getting-started/data-modeling/modeling-designs/ (Accessed: 2026-03-03, Version: Getting Started current)
