"""Pydantic models for FastAPI request/response schemas."""

from pydantic import BaseModel


class SearchRequest(BaseModel):
    role_title: str | None = None
    role_description: str | None = None
    required_skills: list[str] = []
    desired_skills: list[str] = []
    weights: dict[str, float] = {"skill": 0.4, "role": 0.3, "experience": 0.3}
    top_k: int = 10


class CandidateResult(BaseModel):
    person_stable_id: str
    name: str
    current_title: str
    composite_score: float
    skill_score: float
    role_score: float
    experience_score: float
    evidence: str
    matched_skills: list[str]


class SearchResponse(BaseModel):
    candidates: list[CandidateResult]
    query_skills_used: list[str]


class SkillExtractionRequest(BaseModel):
    text: str


class SkillExtractionResponse(BaseModel):
    required_skills: list[str]
    desired_skills: list[str]


class PostingResponse(BaseModel):
    stable_id: str
    req_number: str
    title: str
    description: str
    required_skills: list[str]
    desired_skills: list[str]
