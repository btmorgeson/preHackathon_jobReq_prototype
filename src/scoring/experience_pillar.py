"""Experience pillar — vector search on chunk embeddings."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

TOP_K = 500


def score_experience(
    query_embedding: list[float],
    driver: Any,
) -> dict[str, float]:
    """
    Vector search chunk_embedding_idx with query embedding -> top TOP_K chunks.
    Group by Person, compute average score.
    Returns {person_stable_id: avg_score} for top results.
    """
    with driver.session() as session:
        records = session.run(
            "CALL db.index.vector.queryNodes($idx, $top_k, $embedding) "
            "YIELD node AS chunk, score "
            "MATCH (p:Person)-[:HAS_CHUNK]->(chunk) "
            "RETURN p.stable_id AS person_id, avg(score) AS avg_score "
            "ORDER BY avg_score DESC",
            idx="chunk_embedding_idx",
            top_k=TOP_K,
            embedding=query_embedding,
        ).data()

    return {r["person_id"]: r["avg_score"] for r in records}
