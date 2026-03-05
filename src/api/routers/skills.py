"""POST /api/extract-skills — dual-LLM skill extraction endpoint."""

import json
import logging
import os

import httpx
from fastapi import APIRouter
from openai import OpenAI

from src.api.models import SkillExtractionRequest, SkillExtractionResponse

logger = logging.getLogger(__name__)
router = APIRouter()

SSL_CERT = os.environ.get("SSL_CERT_FILE", "C:/Users/e477258/combined_pem.pem")
GENESIS_BASE_URL = "https://api.ai.us.lmco.com/v1"
GENESIS_ORG = "SKLZ"
REASONING_MODEL = "claude-4-5-sonnet-latest"
EXTRACTION_MODEL = "gpt-oss-120b"

SKILL_EXTRACTION_SCHEMA = {
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
}


def _make_genesis_client() -> OpenAI:
    key = os.environ["GENESIS_SKLZ_API_KEY"]
    return OpenAI(
        base_url=GENESIS_BASE_URL,
        api_key=key,
        default_headers={"openai-organization": GENESIS_ORG},
        http_client=httpx.Client(verify=SSL_CERT),
    )


@router.post("/extract-skills", response_model=SkillExtractionResponse)
def extract_skills(request: SkillExtractionRequest) -> SkillExtractionResponse:
    """
    Step 1: Claude reasons about required/desired skills from raw text.
    Step 2: GPT extracts structured JSON via json_schema response_format.
    """
    client = _make_genesis_client()

    # Step 1: Claude reasoning
    claude_prompt = (
        "Extract the required and desired skills from the following job description. "
        "List them clearly.\n\n" + request.text
    )
    logger.info("Calling Claude for skill reasoning, text length=%d", len(request.text))
    claude_response = client.chat.completions.create(
        model=REASONING_MODEL,
        messages=[{"role": "user", "content": claude_prompt}],
    )
    claude_text = claude_response.choices[0].message.content or ""
    logger.info("Claude skill reasoning complete, output length=%d", len(claude_text))

    # Step 2: GPT structured extraction
    gpt_prompt = (
        "From the following skill analysis, extract required_skills and desired_skills "
        "as separate JSON arrays.\n\n" + claude_text
    )
    logger.info("Calling GPT for structured skill extraction")
    gpt_response = client.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=[{"role": "user", "content": gpt_prompt}],
        response_format={"type": "json_schema", "json_schema": SKILL_EXTRACTION_SCHEMA},
    )
    raw_json = gpt_response.choices[0].message.content or "{}"
    logger.info("GPT extraction complete")

    parsed = json.loads(raw_json)
    return SkillExtractionResponse(
        required_skills=parsed.get("required_skills", []),
        desired_skills=parsed.get("desired_skills", []),
    )
