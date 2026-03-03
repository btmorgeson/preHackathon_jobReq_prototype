# Versioning and Lineage

## Required Version Fields
- `raw_version`
- `transform_version`
- `iceberg_snapshot_id`
- `graph_export_version`
- `embedding_version`

## Lineage Chain
`raw manifest entry -> parquet artifact -> iceberg snapshot -> graph CSV export -> neo4j import batch -> chunk/embedding generation`

## Replay Strategy
- Keep transformation code version (git SHA) with exported artifacts.
- Use deterministic `stable_id` generation so re-runs produce comparable diffs.
- Record import batch timestamp and source snapshot IDs in Neo4j admin/audit nodes.

## Drift Controls
- Detect schema drift before conversion.
- Alert on row-count deltas outside expected bounds.
- Re-embed when model version changes.
