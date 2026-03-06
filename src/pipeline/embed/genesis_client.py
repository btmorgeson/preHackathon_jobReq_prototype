"""Genesis API client for embeddings."""

from __future__ import annotations

import logging
import time

import httpx
from openai import OpenAI

from src.config import get_settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 25


def make_client() -> OpenAI:
    settings = get_settings()
    if not settings.genesis_api_key:
        raise RuntimeError("GENESIS_SKLZ_API_KEY is not set.")

    return OpenAI(
        base_url=settings.genesis_base_url,
        api_key=settings.genesis_api_key,
        default_headers={"openai-organization": settings.genesis_org},
        http_client=httpx.Client(verify=settings.ssl_cert_file),
    )


def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts with exponential backoff on rate limit (429)."""
    settings = get_settings()
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                model=settings.genesis_embedding_model,
                input=texts,
            )
            return [data.embedding for data in response.data]
        except Exception as exc:
            if attempt < max_retries - 1 and "429" in str(exc):
                wait_seconds = 2**attempt
                logger.warning("Rate limit hit, retrying in %ds...", wait_seconds)
                time.sleep(wait_seconds)
            else:
                raise
    raise RuntimeError("embed_batch: max retries exceeded")
