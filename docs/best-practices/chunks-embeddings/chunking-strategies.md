# Chunking Strategies

## Strategy Options
1. Fixed-size token chunks with overlap.
2. Structure-aware chunks (headings/sections/paragraphs).
3. Hybrid: structure-aware first, fixed-size fallback.

## Suggested Starter Policy
- Inference: start around 300-600 tokens with 10-20% overlap for mixed job posting text.
- Reason: no universal official value; tune via retrieval metrics.

## Required Metadata Per Chunk
- `chunk_id`, `doc_id`
- `start_offset`, `end_offset`
- `token_count`
- `language`
- `chunker_name`, `chunker_version`
- `created_at`

## Dedup Rules
- Hash normalized chunk text (`chunk_text_sha256`).
- Prevent duplicate ingestion by unique constraint on (`doc_id`, `start_offset`, `end_offset`, `embedding_version`).

## PII Considerations
- Run pre-chunk redaction checks for sensitive fields.
- Mark redaction state in chunk metadata.
