"""Pydantic models for FastAPI request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from src.config import get_settings


_settings = get_settings()


class SearchWeights(BaseModel):
    skill: float = Field(default=0.4, ge=0.0, le=1.0)
    role: float = Field(default=0.3, ge=0.0, le=1.0)
    experience: float = Field(default=0.3, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_non_zero(self) -> "SearchWeights":
        if (self.skill + self.role + self.experience) <= 0:
            raise ValueError("At least one weight must be greater than zero.")
        return self

    def normalized(self) -> dict[str, float]:
        total = self.skill + self.role + self.experience
        return {
            "skill": self.skill / total,
            "role": self.role / total,
            "experience": self.experience / total,
        }


class QueryContext(BaseModel):
    posting_title: str | None = None
    posting_description: str | None = None


class SearchRequest(BaseModel):
    req_number: str | None = None
    role_title: str | None = None
    role_description: str | None = None
    query_context: QueryContext | None = None
    required_skills: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    weights: SearchWeights = Field(default_factory=SearchWeights)
    top_k: int = Field(default_factory=lambda: _settings.default_top_k, ge=1, le=_settings.max_top_k)

    @model_validator(mode="after")
    def validate_intent(self) -> "SearchRequest":
        context_title = self.query_context.posting_title if self.query_context else None
        context_description = self.query_context.posting_description if self.query_context else None

        has_intent = any(
            [
                self.req_number,
                self.role_title,
                self.role_description,
                context_title,
                context_description,
                self.required_skills,
                self.desired_skills,
            ]
        )
        if not has_intent:
            raise ValueError(
                "Provide at least one of req_number, role_title, role_description, "
                "query_context, required_skills, or desired_skills."
            )
        return self


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
    request_id: str
    candidates: list[CandidateResult]
    query_skills_used: list[str]
    timings_ms: dict[str, float]


class SkillExtractionRequest(BaseModel):
    text: str = Field(min_length=1)


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


class ErrorPayload(BaseModel):
    code: str
    message: str
    request_id: str
    details: object | None = None


class ErrorResponse(BaseModel):
    error: ErrorPayload
