# Ingestion Pipeline: Document -> Chunk -> Embed -> Store -> Link

## Default Flow (Neo4j GraphRAG)
1. Ingest source document metadata (`doc_id`, `source_uri`, `version`).
2. Split into chunks (fixed-size or semantic boundaries).
3. Generate embeddings.
4. Write `Chunk` nodes with text, offsets, and embedding metadata.
5. Link chunks to entities (`Skill`, `Role`, `Org`, `Posting`) with `MENTIONS` edges.

## Canonical Chunk Schema
- `chunk_id`
- `doc_id`
- `text`
- `token_count`
- `start_offset`
- `end_offset`
- `embedding_model`
- `embedding_dim`
- `embedding_version`
- `created_at`

## Relationship Schema
```text
(:Chunk)-[:MENTIONS {confidence, extractor_version, is_inferred}]->(:Skill|:Role|:Org|:Posting)
```

## Alternate Flows
- Alternate A: Neo4j GenAI plugin procedures generate embeddings in database.
- Alternate B: External Python pipeline computes embeddings and writes vectors via driver.

## Inference Notes
- Inference: Best chunk sizes/overlap values are workload dependent; Neo4j GraphRAG docs provide splitter components but not universal numeric defaults.
