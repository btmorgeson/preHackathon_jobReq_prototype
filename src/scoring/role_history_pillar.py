"""Role history pillar — vector search on role titles with recency decay."""

import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

RECENCY_DECAY = 0.85
TOP_K = 200


def score_role_history(
    query_embedding: list[float],
    driver: Any,
) -> dict[str, float]:
    """
    Vector search role_title_idx with query embedding -> top TOP_K roles.
    Group by Person, apply recency decay: score * (RECENCY_DECAY ^ position_from_most_recent)
    position 0 = most recent (current role), higher = older.
    Returns {person_stable_id: max_decayed_score}
    """
    with driver.session() as session:
        records = session.run(
            "CALL db.index.vector.queryNodes($idx, $top_k, $embedding) "
            "YIELD node AS role, score "
            "MATCH (p:Person)-[:HAS_ROLE]->(role) "
            "RETURN p.stable_id AS person_id, role.is_current AS is_current, "
            "       role.start_date AS start_date, score "
            "ORDER BY person_id, is_current DESC, start_date DESC",
            idx="role_title_idx",
            top_k=TOP_K,
            embedding=query_embedding,
        ).data()

    # Group roles by person, preserving order (most recent first)
    person_roles: dict[str, list[float]] = defaultdict(list)
    for r in records:
        person_roles[r["person_id"]].append(r["score"])

    scores: dict[str, float] = {}
    for pid, role_scores in person_roles.items():
        # Apply recency decay: most recent role (index 0) gets full score
        decayed = max(
            s * (RECENCY_DECAY ** i) for i, s in enumerate(role_scores)
        )
        scores[pid] = decayed

    return scores
