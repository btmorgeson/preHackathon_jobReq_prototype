"""POST /api/search — candidate ranking endpoint."""

import logging
from fastapi import APIRouter, Depends
from neo4j import Driver

from src.api.models import SearchRequest, SearchResponse, CandidateResult
from src.api.deps import get_driver
from src.pipeline.embed.genesis_client import make_client, embed_batch
from src.scoring.aggregator import aggregate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search_candidates(request: SearchRequest, driver: Driver = Depends(get_driver)) -> SearchResponse:
    """Embed query text, run three-pillar scoring, return ranked candidates."""
    parts = []
    if request.role_title:
        parts.append(request.role_title)
    if request.role_description:
        parts.append(request.role_description)
    parts.extend(request.required_skills)

    query_text = " ".join(parts) if parts else "software engineer"
    logger.info("Search query text: %s", query_text[:120])

    client = make_client()
    embeddings = embed_batch(client, [query_text])
    query_embedding = embeddings[0]

    results = aggregate(
        query_embedding=query_embedding,
        required_skills=request.required_skills,
        desired_skills=request.desired_skills,
        driver=driver,
        weights=request.weights,
        top_k=request.top_k,
    )

    candidates = [
        CandidateResult(
            person_stable_id=r.person_stable_id,
            name=r.name,
            current_title=r.current_title,
            composite_score=r.composite_score,
            skill_score=r.skill_score,
            role_score=r.role_score,
            experience_score=r.experience_score,
            evidence=r.evidence,
            matched_skills=r.matched_skills,
        )
        for r in results
    ]

    query_skills_used = request.required_skills + request.desired_skills

    return SearchResponse(candidates=candidates, query_skills_used=query_skills_used)
