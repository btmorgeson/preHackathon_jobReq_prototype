# Data Storage Approach

## Layout
- `data/raw/`: immutable source drops and metadata manifests.
- `data/staged/`: intermediate clean files (for example normalized CSV/JSON) before parquet.
- `data/parquet/`: parquet outputs used for analytical and Iceberg ingestion paths.
- `data/iceberg/`: optional local object-storage mirror for testing (normally external object store).
- `data/exports/graph/`: node/edge CSV files for Neo4j bulk import.
- `data/embeddings/`: optional local embedding cache artifacts (not for git).

## Rules
- Raw files are append-only and never edited in place.
- Every raw file should have a manifest entry with checksum and source URL.
- Large files remain out of git; keep only tiny fixtures/samples for tests.
- Graph outputs are reproducible derivatives and can be regenerated.

## Retention
- Keep raw manifests long-term.
- Expire staged/transient files aggressively.
- Rebuild embeddings when model/version changes (see docs on embedding versioning).
