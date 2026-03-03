# Neo4j GraphRAG

## Purpose
Explain how chunked text, embeddings, and entity links are stored and retrieved in Neo4j for GraphRAG workflows.

## What You'll Learn
- Default GraphRAG ingestion path for this prototype.
- How vector indexes and graph expansion work together.
- How to keep retrieval grounded with source lineage.

## Prerequisites
- Neo4j running locally.
- Imported graph entities (`Skill`, `Role`, `Posting`) and chunk/doc nodes.
- Embedding model selection and dimension values finalized.

## Quickstart
1. Create vector index using [`vector-indexes.md`](vector-indexes.md).
2. Ingest chunk nodes and `MENTIONS` links via [`ingestion-pipeline.md`](ingestion-pipeline.md).
3. Run hybrid retrieval query from [`retrieval-patterns.md`](retrieval-patterns.md).

## Deep Dive
- Official source registry: [`official-sources.md`](official-sources.md)
- Ingestion design: [`ingestion-pipeline.md`](ingestion-pipeline.md)
- Retrieval patterns: [`retrieval-patterns.md`](retrieval-patterns.md)
- Failure patterns: [`gotchas.md`](gotchas.md)

## Common Mistakes / Gotchas
- Embedding dimensions in data not matching vector index dimensions.
- Omitting `doc_id`, offsets, and version fields from chunk nodes.
- Using vector-only retrieval without graph neighborhood expansion.

## Official Sources
- Neo4j GraphRAG Python docs: https://neo4j.com/docs/neo4j-graphrag-python/current/ (Accessed: 2026-03-03, Version: current docs branch)
- Neo4j vector indexes: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/ (Accessed: 2026-03-03, Version: Cypher Manual current)
- Neo4j GenAI integrations: https://neo4j.com/docs/cypher-manual/current/genai-integrations/ (Accessed: 2026-03-03, Version: Cypher Manual current)
