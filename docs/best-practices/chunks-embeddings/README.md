# Chunks and Embeddings Best Practices

## Purpose
Set standards for chunking, embedding, versioning, and retrieval quality for GraphRAG.

## What You'll Learn
- How to choose chunking strategies and overlap policies.
- How to version embeddings and plan re-embedding.
- How to evaluate retrieval quality over time.

## Prerequisites
- Chunk schema and vector index design from GraphRAG docs.
- Defined embedding model and dimensions.

## Quickstart
1. Start with a simple chunking policy from [`chunking-strategies.md`](chunking-strategies.md).
2. Track model metadata per chunk using [`embedding-versioning.md`](embedding-versioning.md).
3. Run retrieval evaluation loops in [`eval-and-quality.md`](eval-and-quality.md).

## Deep Dive
- Chunk design and metadata contracts.
- Embedding migration and compatibility.
- Retrieval KPIs and drift checks.

## Common Mistakes / Gotchas
- Treating chunk size defaults as universal across corpora.
- Omitting offset metadata required for answer citations.
- Mixing embeddings from different models in one index.

## Official Sources
- Neo4j GraphRAG KG builder and text splitting: https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html (Accessed: 2026-03-03, Version: current docs branch)
- Neo4j vector index docs: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/ (Accessed: 2026-03-03, Version: Cypher Manual current)
- OpenAI embeddings guide: https://platform.openai.com/docs/guides/embeddings (Accessed: 2026-03-03, Version: Docs current)
