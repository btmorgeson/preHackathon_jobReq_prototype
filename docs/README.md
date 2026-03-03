# Prototype Knowledge Pack: Raw -> Parquet -> Iceberg -> Graph CSV -> Neo4j -> GraphRAG

## Purpose
This documentation pack provides a reproducible, official-source-first path to stand up a prototype data pipeline from raw datasets to Neo4j GraphRAG.

## What You'll Learn
- How to source US-only datasets safely and legally.
- How to stage raw files, convert to Parquet, and register Iceberg tables.
- How to export graph-shaped CSV nodes/edges and bulk import into Neo4j.
- How to build chunk + embedding + entity-link workflows for Neo4j GraphRAG.

## Prerequisites
- Docker Engine + Docker Compose v2.
- `curl`, `jq`, and a shell (`bash`/`zsh`/PowerShell equivalent).
- Optional: `duckdb`, Python 3.10+, Java 17 (for local Spark tooling).

## Quickstart
1. Start local infra:
   - `docker compose up -d`
2. Review datasets and small-sample fetch workflow:
   - [`datasets/README.md`](datasets/README.md)
   - [`scripts/fetch_datasets.md`](../scripts/fetch_datasets.md)
3. Convert samples to parquet:
   - [`scripts/convert_to_parquet.md`](../scripts/convert_to_parquet.md)
4. Build Iceberg tables:
   - [`scripts/build_iceberg_tables.md`](../scripts/build_iceberg_tables.md)
5. Export graph CSVs + bulk import:
   - [`scripts/export_graph_csv.md`](../scripts/export_graph_csv.md)
   - [`scripts/neo4j_bulk_import.md`](../scripts/neo4j_bulk_import.md)
6. Enable GraphRAG retrieval flow:
   - [`graphrag/neo4j/README.md`](graphrag/neo4j/README.md)

## Deep Dive
### Recommended Reading Order
1. [`datasets/README.md`](datasets/README.md)
2. [`data-layers/raw/README.md`](data-layers/raw/README.md) and [`data-layers/parquet/README.md`](data-layers/parquet/README.md)
3. [`otf/iceberg/README.md`](otf/iceberg/README.md)
4. [`data-layers/graph-export/README.md`](data-layers/graph-export/README.md)
5. [`neo4j/csv-import-bulk.md`](neo4j/csv-import-bulk.md)
6. [`graphrag/neo4j/README.md`](graphrag/neo4j/README.md)
7. [`best-practices/large-text/README.md`](best-practices/large-text/README.md) and [`best-practices/chunks-embeddings/README.md`](best-practices/chunks-embeddings/README.md)

### Full Directory Map
- Neo4j
  - [`neo4j/README.md`](neo4j/README.md)
  - [`neo4j/official-sources.md`](neo4j/official-sources.md)
  - [`neo4j/local-setup-docker.md`](neo4j/local-setup-docker.md)
  - [`neo4j/csv-import-bulk.md`](neo4j/csv-import-bulk.md)
  - [`neo4j/cypher-patterns.md`](neo4j/cypher-patterns.md)
  - [`neo4j/gotchas.md`](neo4j/gotchas.md)
- Datasets
  - [`datasets/README.md`](datasets/README.md)
  - [`datasets/people-and-skills.md`](datasets/people-and-skills.md)
  - [`datasets/job-postings-text.md`](datasets/job-postings-text.md)
  - [`datasets/role-history.md`](datasets/role-history.md)
  - [`datasets/licenses-and-ethics.md`](datasets/licenses-and-ethics.md)
  - [`datasets/schema-notes.md`](datasets/schema-notes.md)
- Data layers
  - [`data-layers/raw/README.md`](data-layers/raw/README.md)
  - [`data-layers/raw/naming-and-manifests.md`](data-layers/raw/naming-and-manifests.md)
  - [`data-layers/parquet/README.md`](data-layers/parquet/README.md)
  - [`data-layers/parquet/conversion-guide.md`](data-layers/parquet/conversion-guide.md)
  - [`data-layers/graph-export/README.md`](data-layers/graph-export/README.md)
  - [`data-layers/graph-export/node-tables.md`](data-layers/graph-export/node-tables.md)
  - [`data-layers/graph-export/edge-tables.md`](data-layers/graph-export/edge-tables.md)
  - [`data-layers/graph-export/neo4j-import-mapping.md`](data-layers/graph-export/neo4j-import-mapping.md)
- OTF / Iceberg
  - [`otf/iceberg/README.md`](otf/iceberg/README.md)
  - [`otf/iceberg/official-sources.md`](otf/iceberg/official-sources.md)
  - [`otf/iceberg/local-lakehouse-minio.md`](otf/iceberg/local-lakehouse-minio.md)
  - [`otf/iceberg/write-read-examples.md`](otf/iceberg/write-read-examples.md)
  - [`otf/iceberg/partitioning-compaction.md`](otf/iceberg/partitioning-compaction.md)
  - [`otf/iceberg/gotchas.md`](otf/iceberg/gotchas.md)
- GraphRAG
  - [`graphrag/neo4j/README.md`](graphrag/neo4j/README.md)
  - [`graphrag/neo4j/official-sources.md`](graphrag/neo4j/official-sources.md)
  - [`graphrag/neo4j/ingestion-pipeline.md`](graphrag/neo4j/ingestion-pipeline.md)
  - [`graphrag/neo4j/vector-indexes.md`](graphrag/neo4j/vector-indexes.md)
  - [`graphrag/neo4j/retrieval-patterns.md`](graphrag/neo4j/retrieval-patterns.md)
  - [`graphrag/neo4j/gotchas.md`](graphrag/neo4j/gotchas.md)
- Best practices
  - [`best-practices/large-text/README.md`](best-practices/large-text/README.md)
  - [`best-practices/large-text/storage-patterns.md`](best-practices/large-text/storage-patterns.md)
  - [`best-practices/large-text/versioning-and-lineage.md`](best-practices/large-text/versioning-and-lineage.md)
  - [`best-practices/chunks-embeddings/README.md`](best-practices/chunks-embeddings/README.md)
  - [`best-practices/chunks-embeddings/chunking-strategies.md`](best-practices/chunks-embeddings/chunking-strategies.md)
  - [`best-practices/chunks-embeddings/embedding-versioning.md`](best-practices/chunks-embeddings/embedding-versioning.md)
  - [`best-practices/chunks-embeddings/eval-and-quality.md`](best-practices/chunks-embeddings/eval-and-quality.md)

### Architecture Diagram (ASCII)
```text
US datasets (APIs/files)
        |
        v
[data/raw] -- manifests/checksums --> [data/staged parquet]
        |                                   |
        |                                   v
        |                             Iceberg tables
        |                              (REST catalog
        |                               + MinIO)
        |                                   |
        +---------------------------> graph export (CSV nodes/edges)
                                            |
                                            v
                                   neo4j-admin bulk import
                                            |
                                            v
                             Neo4j graph + vector index + GraphRAG
```

### Platform Notes
- macOS/Linux: commands in this pack run as written (bash/zsh).
- Windows: use WSL2 when possible; for PowerShell, adapt path separators and quoting.

## Common Mistakes / Gotchas
- Downloading entire datasets into git-tracked paths.
- Mixing mutable and immutable raw files.
- Storing full raw text in core domain nodes instead of chunk/document nodes.
- Running `neo4j-admin import` against a running Neo4j DBMS.

## Official Sources
- Neo4j Docker + operations manual: https://neo4j.com/docs/operations-manual/current/docker/introduction/ (Accessed: 2026-03-03, Version: Neo4j 2026.01 docs branch)
- Apache Iceberg docs: https://iceberg.apache.org/docs/latest/ (Accessed: 2026-03-03, Version: Latest shows 1.10.1)
- Neo4j GraphRAG Python docs: https://neo4j.com/docs/neo4j-graphrag-python/current/ (Accessed: 2026-03-03, Version: current docs branch)
- USAJOBS developer docs: https://developer.usajobs.gov/ (Accessed: 2026-03-03, Version: N/A)
