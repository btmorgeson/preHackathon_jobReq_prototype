# Neo4j Gotchas

## Bulk Import Pitfalls
- `neo4j-admin` import only supports offline initial load for the target database.
- Header/type mismatch produces hard-to-diagnose row parse errors.
- Duplicate IDs can silently route to error files if bad-tolerance flags are enabled.

## Schema Pitfalls
- Missing uniqueness constraints can create duplicate business entities.
- Creating vector indexes before embeddings exist causes misleading empty-search results.

## Platform Pitfalls
- Windows CSV tools may inject BOM/CRLF; validate with `file` or `hexdump`.
- Low Docker memory limits lead to startup/import instability.

## Operational Pitfalls
- Forgetting to preserve source provenance (`source_system`, `source_id`, `stable_id`) makes replays and audits difficult.
- Failing to version extractor/embedding metadata makes regressions hard to debug.
