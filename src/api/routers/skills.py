"""POST /api/extract-skills — skill extraction endpoint using Genesis dual-LLM."""

from __future__ import annotations

import json
import logging
import re

import httpx
from fastapi import APIRouter
from openai import OpenAI

from src.api.models import SkillExtractionRequest, SkillExtractionResponse
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _make_genesis_client() -> OpenAI | None:
    """Return Genesis OpenAI client, or None if API key is not configured."""
    settings = get_settings()
    if not settings.genesis_api_key:
        logger.warning("GENESIS_SKLZ_API_KEY not set — skill extraction will use keyword fallback")
        return None
    return OpenAI(
        base_url=settings.genesis_base_url,
        api_key=settings.genesis_api_key,
        default_headers={"openai-organization": settings.genesis_org},
        http_client=httpx.Client(verify=settings.ssl_cert_file),
    )


def _extract_with_genesis(text: str, client: OpenAI) -> dict:
    """
    Dual-LLM skill extraction:
      1. Claude (claude-4-5-sonnet-latest) — reason about what skills are required vs desired
      2. GPT (gpt-oss-120b) — structured JSON output via json_schema response format
    Returns {"required_skills": [...], "desired_skills": [...]}
    """
    settings = get_settings()

    # Step 1: Claude for reasoning (plain text, no json_schema — Claude 500s on json_schema)
    reasoning_prompt = (
        "You are an HR analyst. Read the following job description and identify:\n"
        "1. REQUIRED skills: skills explicitly marked as required, must-have, or minimum qualifications\n"
        "2. DESIRED skills: skills marked as preferred, nice-to-have, or bonus qualifications\n\n"
        "List each skill as a short noun phrase (e.g., 'Python', 'Project Management', 'AWS').\n"
        "Be concise. Output format:\n"
        "REQUIRED: skill1, skill2, skill3\n"
        "DESIRED: skill4, skill5\n\n"
        f"Job description:\n{text[:3000]}"
    )

    reasoning_response = client.chat.completions.create(
        model=settings.genesis_reasoning_model,
        messages=[{"role": "user", "content": reasoning_prompt}],
        max_tokens=500,
        temperature=0,
    )
    reasoning_text = reasoning_response.choices[0].message.content or ""
    logger.debug("Claude reasoning output: %s", reasoning_text[:200])

    # Step 2: GPT for structured JSON extraction from Claude's reasoning
    extraction_prompt = (
        "Convert the following skill analysis into structured JSON with exactly two keys: "
        "'required_skills' (array of strings) and 'desired_skills' (array of strings). "
        "Each skill should be a clean, short noun phrase. "
        "Remove duplicates. Do not include empty strings.\n\n"
        f"Skill analysis:\n{reasoning_text}"
    )

    extraction_response = client.chat.completions.create(
        model=settings.genesis_extraction_model,
        messages=[{"role": "user", "content": extraction_prompt}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "skill_extraction",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "required_skills": {"type": "array", "items": {"type": "string"}},
                        "desired_skills": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["required_skills", "desired_skills"],
                    "additionalProperties": False,
                },
            },
        },
        max_tokens=500,
        temperature=0,
    )

    content = extraction_response.choices[0].message.content or "{}"
    result = json.loads(content)
    return {
        "required_skills": [s.strip() for s in result.get("required_skills", []) if s.strip()],
        "desired_skills": [s.strip() for s in result.get("desired_skills", []) if s.strip()],
    }


def _extract_keywords(text: str) -> dict:
    """
    Fallback keyword-based skill extraction using regex patterns.
    Handles common formats like 'Required: X, Y' and 'Nice to have: X, Y'.
    """
    required: list[str] = []
    desired: list[str] = []

    # Required patterns
    req_patterns = [
        r"(?:required|must[- ]have|minimum qualifications?|requirements?)[:\s]+([^\n]{5,200})",
        r"(?:you must have|candidates? must)[:\s]+([^\n]{5,200})",
    ]
    # Desired patterns
    des_patterns = [
        r"(?:desired|preferred|nice[- ]to[- ]have|bonus|plus|ideally)[:\s]+([^\n]{5,200})",
        r"(?:would be great|beneficial|advantageous)[:\s]+([^\n]{5,200})",
    ]

    def _parse_skills(match_text: str) -> list[str]:
        """Split comma/semicolon/bullet separated skills."""
        parts = re.split(r"[,;•·\n]+", match_text)
        skills = []
        for part in parts:
            cleaned = re.sub(r"^[-*•\s]+", "", part).strip()
            # Filter out long sentences (they're not skill names)
            if cleaned and 2 <= len(cleaned) <= 60:
                skills.append(cleaned)
        return skills

    text_lower = text.lower()
    for pattern in req_patterns:
        for m in re.finditer(pattern, text_lower, re.IGNORECASE):
            required.extend(_parse_skills(text[m.start(1) : m.end(1)]))

    for pattern in des_patterns:
        for m in re.finditer(pattern, text_lower, re.IGNORECASE):
            desired.extend(_parse_skills(text[m.start(1) : m.end(1)]))

    # De-duplicate, preserve order
    seen: set[str] = set()
    unique_required = []
    for s in required:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique_required.append(s)

    unique_desired = []
    for s in desired:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique_desired.append(s)

    # If we got nothing, do a last-resort extraction of bullet points
    if not unique_required and not unique_desired:
        bullets = re.findall(r"^[•*-]\s+(.{3,60})$", text, re.MULTILINE)
        mid = len(bullets) // 2
        unique_required = bullets[:mid]
        unique_desired = bullets[mid:]

    return {"required_skills": unique_required, "desired_skills": unique_desired}


@router.post("/extract-skills", response_model=SkillExtractionResponse)
def extract_skills(request: SkillExtractionRequest) -> SkillExtractionResponse:
    """
    Extract required and desired skills from a job description or role text.
    Uses Genesis dual-LLM (Claude reasoning → GPT JSON) with keyword fallback.
    """
    client = _make_genesis_client()

    if client is not None:
        try:
            result = _extract_with_genesis(request.text, client)
            logger.info(
                "Genesis extraction: %d required, %d desired skills",
                len(result["required_skills"]),
                len(result["desired_skills"]),
            )
            return SkillExtractionResponse(**result)
        except Exception as exc:
            logger.warning("Genesis extraction failed (%s), falling back to keyword extraction", exc)

    # Keyword fallback
    result = _extract_keywords(request.text)
    logger.info(
        "Keyword extraction: %d required, %d desired skills",
        len(result["required_skills"]),
        len(result["desired_skills"]),
    )
    return SkillExtractionResponse(**result)
