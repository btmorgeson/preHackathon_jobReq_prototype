"""Genesis API client for embeddings."""

import os
import time
import logging
import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

SSL_CERT = os.environ.get("SSL_CERT_FILE", "C:/Users/e477258/combined_pem.pem")
os.environ.setdefault("SSL_CERT_FILE", SSL_CERT)
os.environ.setdefault("REQUESTS_CA_BUNDLE", SSL_CERT)

GENESIS_BASE_URL = "https://api.ai.us.lmco.com/v1"
GENESIS_ORG = "SKLZ"
EMBEDDING_MODEL = "mxbai-embed-large-v1"
BATCH_SIZE = 25


def make_client() -> OpenAI:
    key = os.environ["GENESIS_SKLZ_API_KEY"]
    return OpenAI(
        base_url=GENESIS_BASE_URL,
        api_key=key,
        default_headers={"openai-organization": GENESIS_ORG},
        http_client=httpx.Client(verify=SSL_CERT),
    )


def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts with exponential backoff on rate limit (429)."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            return [d.embedding for d in resp.data]
        except Exception as exc:
            if attempt < max_retries - 1 and "429" in str(exc):
                wait = 2 ** attempt
                logger.warning("Rate limit hit, retrying in %ds...", wait)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("embed_batch: max retries exceeded")
