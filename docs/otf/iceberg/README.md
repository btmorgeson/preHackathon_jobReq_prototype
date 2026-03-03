# Apache Iceberg Layer

## Purpose
Document the Open Table Format layer that sits between parquet data and graph export, providing snapshot-based table management and schema evolution.

## What You'll Learn
- Core Iceberg concepts (snapshots, manifests, metadata files, catalogs).
- How to run a local Iceberg REST catalog against MinIO.
- Write/read and maintenance patterns for local prototype tables.

## Prerequisites
- Docker Compose services: `minio`, `iceberg-rest`, and `spark`.
- Parquet sample data from previous steps.

## Quickstart
1. Start local stack: `docker compose up -d minio iceberg-rest spark`.
2. Open Spark shell in container and create table (see [`write-read-examples.md`](write-read-examples.md)).
3. Query table and inspect snapshots.

## Deep Dive
- Concepts and source references: [`official-sources.md`](official-sources.md)
- Local setup details: [`local-lakehouse-minio.md`](local-lakehouse-minio.md)
- Performance/evolution guidance: [`partitioning-compaction.md`](partitioning-compaction.md)
- Common pitfalls: [`gotchas.md`](gotchas.md)

## Common Mistakes / Gotchas
- Using identity partitioning for high-cardinality fields without evaluating file explosion.
- Leaving many tiny files after incremental writes.
- Assuming query-engine defaults are identical across Spark and Trino.

## Official Sources
- Iceberg docs home: https://iceberg.apache.org/docs/latest/ (Accessed: 2026-03-03, Version: Latest shown as 1.10.1)
- Iceberg specification: https://iceberg.apache.org/spec/ (Accessed: 2026-03-03, Version: 1.10.1 spec branch)
- Spark configuration: https://iceberg.apache.org/docs/latest/spark-configuration/ (Accessed: 2026-03-03, Version: 1.10.1 docs branch)
