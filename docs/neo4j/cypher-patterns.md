# Cypher Patterns for Demo Paths

## Person -> Role -> Skill -> Posting
```cypher
MATCH (p:Person)-[:HAS_ROLE]->(r:Role)-[:REQUIRES_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(j:Posting)
RETURN p.fullName, r.title, s.name, j.title
LIMIT 25;
```

## Provenance Trace
```cypher
MATCH (j:Posting {stable_id: $posting_id})-[:DERIVED_FROM]->(d:Document)
RETURN j.title, d.doc_id, d.source_uri, d.ingested_at;
```

## Skill Gap Example
```cypher
MATCH (p:Person {stable_id: $person_id})-[:HAS_ROLE]->(:Role)-[:REQUIRES_SKILL]->(s:Skill)
WITH p, collect(DISTINCT s.name) AS current_skills
MATCH (target:Posting {stable_id: $posting_id})-[:REQUIRES_SKILL]->(need:Skill)
WHERE NOT need.name IN current_skills
RETURN need.name AS missing_skill
ORDER BY missing_skill;
```

## GraphRAG Seed Expansion
```cypher
MATCH (c:Chunk)
WHERE c.doc_id = $doc_id
MATCH (c)-[:MENTIONS]->(s:Skill)<-[:REQUIRES_SKILL]-(j:Posting)
RETURN c.chunk_id, collect(DISTINCT s.name) AS mentioned_skills, collect(DISTINCT j.title) AS related_postings
LIMIT 10;
```

## Notes
- Inference: These templates are example starter queries; tune cardinality and index strategy for production workloads.
