# Storage Patterns

## Pattern: Lake as Truth, Graph as Derived
- Raw/lake stores complete documents and immutable source snapshots.
- Graph stores entities, relationships, chunks, and references.
- Derived graph state can be regenerated from lake + transformation logic.

## Reference Model
For every `Document`/`Chunk` node, include:
- `doc_id`
- `source_uri`
- `source_system`
- `source_id`
- `source_checksum` (or pointer to manifest checksum)
- `lineage_version`

## Why This Pattern
- Reduces graph bloat and memory pressure.
- Improves compliance posture (centralized data governance controls).
- Enables deterministic replay and audit.

## Inference
- Inference: exact text-size threshold for graph storage is workload-specific; keep only retrieval-critical chunk text in graph and maintain full source text in lake/object storage.
