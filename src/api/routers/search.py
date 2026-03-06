"""POST /api/search â€” candidate ranking endpoint."""

from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from neo4j import Driver

from src.api.deps import get_driver
from src.api.models import CandidateResult, QueryContext, SearchRequest, SearchResponse
from src.graph.queries import POSTING_BY_REQ_NUMBER, POSTING_REQUIRED_SKILLS
from src.pipeline.embed.genesis_client import embed_batch, make_client
from src.scoring.aggregator import aggregate

logger = logging.getLogger(__name__)
router = APIRouter()


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(value.strip())
    return deduped


def _resolve_posting_context(
    req_number: str,
    query_context: QueryContext | None,
    driver: Driver,
) -> tuple[QueryContext, list[str], list[str]]:
    with driver.session() as session:
        posting_records = session.run(
            POSTING_BY_REQ_NUMBER,
            req_number=req_number,
        ).data()
    if not posting_records:
        raise HTTPException(status_code=404, detail=f"Posting {req_number!r} not found")

    posting = posting_records[0]
    context = QueryContext(
        posting_title=(query_context.posting_title if query_context else None) or posting["title"],
        posting_description=(query_context.posting_description if query_context else None)
        or posting["description"],
    )

    with driver.session() as session:
        skill_records = session.run(
            POSTING_REQUIRED_SKILLS,
            req_number=req_number,
        ).data()
    required_skills = [record["skill_name"] for record in skill_records if record.get("required")]
    desired_skills = [record["skill_name"] for record in skill_records if not record.get("required")]
    return context, required_skills, desired_skills


@router.post("/search", response_model=SearchResponse)
def search_candidates(
    payload: SearchRequest,
    http_request: Request,
    driver: Driver = Depends(get_driver),
) -> SearchResponse:
    """Embed query context, run three-pillar scoring, and return ranked candidates."""
    request_id = getattr(http_request.state, "request_id", str(uuid4()))
    started = time.perf_counter()

    query_context = payload.query_context
    required_skills = list(payload.required_skills)
    desired_skills = list(payload.desired_skills)

    if payload.req_number:
        query_context, posting_required, posting_desired = _resolve_posting_context(
            payload.req_number,
            query_context,
            driver,
        )
        required_skills.extend(posting_required)
        desired_skills.extend(posting_desired)

    required_skills = _dedupe_preserve_order(required_skills)
    desired_skills = _dedupe_preserve_order(desired_skills)

    query_parts: list[str] = []
    if query_context and query_context.posting_title:
        query_parts.append(query_context.posting_title)
    if payload.role_title:
        query_parts.append(payload.role_title)
    if query_context and query_context.posting_description:
        query_parts.append(query_context.posting_description)
    if payload.role_description:
        query_parts.append(payload.role_description)
    query_parts.extend(required_skills)
    query_parts.extend(desired_skills)
    query_text = " ".join(query_parts).strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Search intent resolved to empty query text.")

    logger.info(
        "search.start request_id=%s req_number=%s top_k=%d required=%d desired=%d query_len=%d",
        request_id,
        payload.req_number,
        payload.top_k,
        len(required_skills),
        len(desired_skills),
        len(query_text),
    )

    client = make_client()
    query_embedding = embed_batch(client, [query_text])[0]

    aggregate_output = aggregate(
        query_embedding=query_embedding,
        required_skills=required_skills,
        desired_skills=desired_skills,
        driver=driver,
        weights=payload.weights.normalized(),
        top_k=payload.top_k,
        posting_req_number=payload.req_number,
    )

    candidates = [
        CandidateResult(
            person_stable_id=result.person_stable_id,
            name=result.name,
            current_title=result.current_title,
            composite_score=result.composite_score,
            skill_score=result.skill_score,
            role_score=result.role_score,
            experience_score=result.experience_score,
            evidence=result.evidence,
            matched_skills=result.matched_skills,
        )
        for result in aggregate_output.candidates
    ]
    total_ms = round((time.perf_counter() - started) * 1000, 2)
    timings = {**aggregate_output.timings_ms, "request_total": total_ms}

    logger.info(
        "search.complete request_id=%s candidates=%d total_ms=%.2f",
        request_id,
        len(candidates),
        total_ms,
    )

    return SearchResponse(
        request_id=request_id,
        candidates=candidates,
        query_skills_used=_dedupe_preserve_order(required_skills + desired_skills),
        timings_ms=timings,
    )
