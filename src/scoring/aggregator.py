"""Score aggregator — combine three pillars into composite CandidateResult."""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CandidateResult:
    person_stable_id: str
    name: str
    current_title: str
    composite_score: float
    skill_score: float
    role_score: float
    experience_score: float
    evidence: str
    matched_skills: list[str]


def aggregate(
    query_embedding: list[float],
    required_skills: list[str],
    desired_skills: list[str],
    driver: Any,
    weights: dict[str, float] | None = None,
    top_k: int = 10,
) -> list[CandidateResult]:
    """
    Run all three pillars and combine scores.
    weights defaults to {"skill": 0.4, "role": 0.3, "experience": 0.3}
    Returns sorted list of CandidateResult (desc by composite_score).
    """
    from src.scoring.skill_pillar import score_skills
    from src.scoring.role_history_pillar import score_role_history
    from src.scoring.experience_pillar import score_experience

    if weights is None:
        weights = {"skill": 0.4, "role": 0.3, "experience": 0.3}

    # Get experience candidates (defines the candidate pool)
    exp_scores = score_experience(query_embedding, driver)
    if not exp_scores:
        logger.warning("No experience scores returned — vector index may be empty")
        return []

    candidate_ids = list(exp_scores.keys())

    # Get role scores for candidate pool
    role_scores_all = score_role_history(query_embedding, driver)

    # Get skill scores for candidate pool
    skill_scores = score_skills(candidate_ids, required_skills, desired_skills, driver)

    # Fetch person info
    with driver.session() as session:
        persons = session.run(
            "MATCH (p:Person) WHERE p.stable_id IN $ids "
            "RETURN p.stable_id AS id, p.name AS name, p.current_title AS current_title",
            ids=candidate_ids,
        ).data()
    person_info = {r["id"]: r for r in persons}

    # Fetch top chunk text per person for evidence
    with driver.session() as session:
        chunk_records = session.run(
            "CALL db.index.vector.queryNodes($idx, $top_k, $embedding) "
            "YIELD node AS chunk, score "
            "MATCH (p:Person)-[:HAS_CHUNK]->(chunk) "
            "WHERE p.stable_id IN $ids "
            "RETURN p.stable_id AS person_id, chunk.text AS text, score "
            "ORDER BY score DESC",
            idx="chunk_embedding_idx",
            top_k=top_k * 5,
            embedding=query_embedding,
            ids=candidate_ids,
        ).data()
    evidence_map: dict[str, str] = {}
    for r in chunk_records:
        if r["person_id"] not in evidence_map:
            evidence_map[r["person_id"]] = r["text"]

    # Fetch matched skills per candidate
    with driver.session() as session:
        skill_records = session.run(
            "MATCH (p:Person)-[:HAS_SKILL]->(s:Skill) "
            "WHERE p.stable_id IN $ids "
            "RETURN p.stable_id AS person_id, collect(s.name) AS skills",
            ids=candidate_ids,
        ).data()
    person_skills_map = {r["person_id"]: r["skills"] for r in skill_records}
    all_query_skills_lower = {s.lower() for s in required_skills + desired_skills}

    results = []
    for pid in candidate_ids:
        exp_s = exp_scores.get(pid, 0.0)
        role_s = role_scores_all.get(pid, 0.0)
        skill_s = skill_scores.get(pid, 0.0)

        composite = (
            weights.get("skill", 0.4) * skill_s
            + weights.get("role", 0.3) * role_s
            + weights.get("experience", 0.3) * exp_s
        )

        info = person_info.get(pid, {})
        matched = [
            s for s in person_skills_map.get(pid, [])
            if s.lower() in all_query_skills_lower
        ]

        results.append(CandidateResult(
            person_stable_id=pid,
            name=info.get("name", "Unknown"),
            current_title=info.get("current_title", ""),
            composite_score=round(composite, 4),
            skill_score=round(skill_s, 4),
            role_score=round(role_s, 4),
            experience_score=round(exp_s, 4),
            evidence=evidence_map.get(pid, ""),
            matched_skills=matched,
        ))

    results.sort(key=lambda r: r.composite_score, reverse=True)
    return results[:top_k]
