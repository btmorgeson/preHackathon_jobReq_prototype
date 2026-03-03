# GraphRAG Gotchas

- Dimension mismatch between stored vectors and index config causes failed or invalid retrieval.
- Missing `doc_id` or offsets makes citations unusable in generated answers.
- Duplicated chunks (from repeated ingestion without idempotency) degrade recall quality.
- Inference-only entity links without confidence/version fields reduce trust.
- Index cold starts can make first queries slow; pre-warm with small test queries.
