# Vector Indexes in Neo4j

## Create Vector Index
```cypher
CREATE VECTOR INDEX chunk_embedding_idx IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 3072,
    `vector.similarity_function`: 'cosine'
  }
};
```

## Query Vector Index
```cypher
CALL db.index.vector.queryNodes('chunk_embedding_idx', 10, $queryEmbedding)
YIELD node, score
RETURN node.chunk_id, node.doc_id, score
ORDER BY score DESC;
```

## Maintenance Guidelines
- Keep `vector.dimensions` aligned with `embedding_dim` metadata.
- Rebuild/recreate index when model dimension changes.
- Keep old and new indexes side-by-side during migrations for rollback.

## Official Source
- https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
- Accessed: 2026-03-03
- Version: Cypher Manual current
