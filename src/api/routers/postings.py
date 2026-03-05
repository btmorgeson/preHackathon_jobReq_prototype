"""GET /api/postings/{req_number} — job posting lookup endpoint."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver

from src.api.models import PostingResponse
from src.api.deps import get_driver
from src.graph.queries import POSTING_BY_REQ_NUMBER, POSTING_REQUIRED_SKILLS

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/postings/{req_number}", response_model=PostingResponse)
def get_posting(req_number: str, driver: Driver = Depends(get_driver)) -> PostingResponse:
    """Fetch a job posting and its required/desired skills by req_number."""
    with driver.session() as session:
        posting_records = session.run(
            POSTING_BY_REQ_NUMBER,
            req_number=req_number,
        ).data()

    if not posting_records:
        raise HTTPException(status_code=404, detail=f"Posting {req_number!r} not found")

    posting = posting_records[0]

    with driver.session() as session:
        skill_records = session.run(
            POSTING_REQUIRED_SKILLS,
            req_number=req_number,
        ).data()

    required_skills = [r["skill_name"] for r in skill_records if r.get("required")]
    desired_skills = [r["skill_name"] for r in skill_records if not r.get("required")]

    return PostingResponse(
        stable_id=posting["stable_id"],
        req_number=posting["req_number"],
        title=posting["title"],
        description=posting["description"],
        required_skills=required_skills,
        desired_skills=desired_skills,
    )
