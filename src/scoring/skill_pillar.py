"""Skill matching pillar — exact match against HAS_SKILL edges."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def score_skills(
    person_ids: list[str],
    required_skills: list[str],
    desired_skills: list[str],
    driver: Any,
) -> dict[str, float]:
    """
    For each person_id, compute skill score:
      required skills weight 2x, desired 1x
      score = matched_weight / total_possible_weight -> 0.0-1.0
    Returns {person_stable_id: score}
    """
    if not required_skills and not desired_skills:
        return {pid: 0.0 for pid in person_ids}

    total_weight = len(required_skills) * 2 + len(desired_skills)
    if total_weight == 0:
        return {pid: 0.0 for pid in person_ids}

    required_lower = {s.lower() for s in required_skills}
    desired_lower = {s.lower() for s in desired_skills}

    with driver.session() as session:
        records = session.run(
            "MATCH (p:Person)-[:HAS_SKILL]->(s:Skill) "
            "WHERE p.stable_id IN $ids "
            "RETURN p.stable_id AS person_id, collect(toLower(s.name)) AS skills",
            ids=person_ids,
        ).data()

    scores: dict[str, float] = {}
    person_skills_map = {r["person_id"]: set(r["skills"]) for r in records}

    for pid in person_ids:
        skills = person_skills_map.get(pid, set())
        weight = sum(2 for s in required_lower if s in skills)
        weight += sum(1 for s in desired_lower if s in skills)
        scores[pid] = min(weight / total_weight, 1.0)

    return scores
