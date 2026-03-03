# Retrieval Patterns: Hybrid Vector + Graph Expansion

## Pattern 1: Vector First, Graph Expand
1. Vector search top-k chunks.
2. Expand each chunk to directly linked entities.
3. Expand one more hop to related postings/roles.
4. Assemble final context with provenance fields.

Example query skeleton:
```cypher
CALL db.index.vector.queryNodes('chunk_embedding_idx', 20, $queryEmbedding)
YIELD node AS chunk, score
WITH chunk, score
MATCH (chunk)-[:MENTIONS]->(skill:Skill)
OPTIONAL MATCH (skill)<-[:REQUIRES_SKILL]-(posting:Posting)
RETURN chunk.chunk_id, chunk.doc_id, score,
       collect(DISTINCT skill.name)[0..10] AS skills,
       collect(DISTINCT posting.title)[0..10] AS postings
ORDER BY score DESC
LIMIT 20;
```

## Pattern 2: Entity Seed Then Vector Re-rank
1. Extract entities from query.
2. Find neighborhood in graph.
3. Restrict vector search to related chunks/documents.

## Context Assembly Requirements
Always include:
- `doc_id`
- `source_uri`
- `chunk_id`
- `embedding_version`
- retrieval timestamp
