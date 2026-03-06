"""Score aggregator — combine three pillars into composite CandidateResult.

Delegates to HybridRetriever for graph-seeded candidate pool + vector re-rank.
"""

from __future__ import annotations

import logging
import time
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


@dataclass
class AggregateOutput:
    candidates: list[CandidateResult]
    timings_ms: dict[str, float]


def _normalize_scores(scores: dict[str, float], person_ids: list[str]) -> dict[str, float]:
    values = [scores.get(pid, 0.0) for pid in person_ids]
    if not values:
        return {}
    min_score = min(values)
    max_score = max(values)
    if max_score <= min_score:
        # If every score is identical, preserve "has evidence" as 1.0 and no-evidence as 0.0.
        return {pid: 1.0 if scores.get(pid, 0.0) > 0 else 0.0 for pid in person_ids}
    scale = max_score - min_score
    return {
        pid: (scores.get(pid, 0.0) - min_score) / scale
        for pid in person_ids
    }


def _normalize_weights(weights: dict[str, float] | None) -> dict[str, float]:
    defaults = {"skill": 0.4, "role": 0.3, "experience": 0.3}
    if weights is None:
        return defaults
    merged = {**defaults, **weights}
    total = merged["skill"] + merged["role"] + merged["experience"]
    if total <= 0:
        return defaults
    return {
        "skill": merged["skill"] / total,
        "role": merged["role"] / total,
        "experience": merged["experience"] / total,
    }


def aggregate(
    query_embedding: list[float],
    required_skills: list[str],
    desired_skills: list[str],
    driver: Any,
    weights: dict[str, float] | None = None,
    top_k: int = 10,
    *,
    posting_req_number: str | None = None,
    use_llm_evidence: bool = True,
) -> AggregateOutput:
    """Run graph-seeded hybrid retrieval and return ranked CandidateResult list.

    Two new keyword-only params (backward-compatible — existing callers unaffected):
        posting_req_number: enables posting-based graph seed when set.
        use_llm_evidence:   set False to skip the LLM call (faster, raw chunk text).
    """
    from src.graph.hybrid_retriever import HybridRetriever
    from src.pipeline.embed.genesis_client import make_client

    normalized_weights = _normalize_weights(weights)

    client = make_client()
    retriever = HybridRetriever(driver, client)

    hybrid_results, stage_timings = retriever.retrieve(
        query_embedding=query_embedding,
        posting_req_number=posting_req_number,
        required_skills=required_skills,
        desired_skills=desired_skills,
        weights=normalized_weights,
        top_k=top_k,
        use_llm_evidence=use_llm_evidence,
    )

    if not hybrid_results:
        logger.warning("HybridRetriever returned no results — check graph seed and vector indexes.")
        timings = {**stage_timings, "total": sum(stage_timings.values())}
        return AggregateOutput(
            candidates=[],
            timings_ms={k: round(v, 2) for k, v in timings.items()},
        )

    results: list[CandidateResult] = [
        CandidateResult(
            person_stable_id=r.person_stable_id,
            name=r.name,
            current_title=r.current_title,
            composite_score=r.composite_score,
            skill_score=r.graph_skill_score,
            role_score=r.role_score,
            experience_score=r.vector_chunk_score,
            evidence=r.evidence,
            matched_skills=r.matched_skills,
        )
        for r in hybrid_results
    ]

    timings = {**stage_timings, "total": sum(stage_timings.values())}
    return AggregateOutput(
        candidates=results,
        timings_ms={k: round(v, 2) for k, v in timings.items()},
    )
