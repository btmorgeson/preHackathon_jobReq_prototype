# Embedding Versioning

## Mandatory Fields
- `embedding_model`
- `embedding_dim`
- `embedding_version`
- `embedded_at`

## Versioning Rules
- Increment `embedding_version` when model, preprocessing, or chunking changes.
- Keep old vectors during migration and compare retrieval quality before cutover.

## Re-Embedding Triggers
- Model upgrade/dimension change.
- Significant corpus drift.
- Changes in chunking or normalization logic.

## Compatibility
- One vector index per embedding dimension/model family.
- Keep index name versioned (for example `chunk_embedding_v1_idx`, `chunk_embedding_v2_idx`).
