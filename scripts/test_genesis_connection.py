"""
Genesis API Connectivity Test — 4-phase progressive verification.

Usage:
    python scripts/test_genesis_connection.py
    python scripts/test_genesis_connection.py --verbose

Requires:
    GENESIS_SKLZ_API_KEY — system env var (set via setx, not .env)

Dependencies:
    pip install openai httpx
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import httpx

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings  # noqa: E402

settings = get_settings()
SSL_CERT = settings.ssl_cert_file
os.environ.setdefault("SSL_CERT_FILE", settings.ssl_cert_file)
os.environ.setdefault("REQUESTS_CA_BUNDLE", settings.ssl_cert_file)

from openai import OpenAI  # noqa: E402 — after env setup

logger = logging.getLogger(__name__)

GENESIS_BASE_URL = settings.genesis_base_url
GENESIS_ORG = settings.genesis_org
REASONING_MODEL = settings.genesis_reasoning_model
EXTRACTION_MODEL = settings.genesis_extraction_model
EMBEDDING_MODEL = settings.genesis_embedding_model
EMBEDDING_DIMS = 1024


def _get_api_key() -> str:
    key = settings.genesis_api_key or ""
    if not key:
        raise EnvironmentError(
            "GENESIS_SKLZ_API_KEY is not set. "
            "Set it with: setx GENESIS_SKLZ_API_KEY <your-token> "
            "(then open a new terminal)"
        )
    return key


def _make_client(api_key: str) -> OpenAI:
    return OpenAI(
        base_url=GENESIS_BASE_URL,
        api_key=api_key,
        default_headers={"openai-organization": GENESIS_ORG},
        http_client=httpx.Client(verify=SSL_CERT),
    )


# ---------------------------------------------------------------------------
# Phase 1 — Raw HTTP models list
# ---------------------------------------------------------------------------

def phase1_raw_http(api_key: str) -> bool:
    """Validate network path, auth, and model availability via raw HTTP."""
    print("\nPHASE 1 — Raw HTTP models list")
    start = time.time()
    try:
        with httpx.Client(verify=SSL_CERT) as http:
            resp = http.get(
                f"{GENESIS_BASE_URL}/models",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "openai-organization": GENESIS_ORG,
                },
                timeout=30.0,
            )
        elapsed = int((time.time() - start) * 1000)

        if resp.status_code != 200:
            print(f"  FAIL — HTTP {resp.status_code}: {resp.text[:200]}")
            return False

        models = resp.json().get("data", [])
        model_ids = [m["id"] for m in models]
        print(f"  OK   — HTTP 200, {len(models)} models available ({elapsed}ms)")

        for required in (REASONING_MODEL, EXTRACTION_MODEL, EMBEDDING_MODEL):
            if required in model_ids:
                print(f"  OK   — Model found: {required}")
            else:
                print(f"  WARN — Model NOT found: {required}")
                print(f"         Available: {', '.join(model_ids[:10])} ...")

        return True

    except Exception as exc:
        print(f"  FAIL — {exc}")
        logger.exception("Phase 1 failed")
        return False


# ---------------------------------------------------------------------------
# Phase 2 — OpenAI SDK basic chat (Claude reasoning model)
# ---------------------------------------------------------------------------

def phase2_basic_chat(client: OpenAI) -> bool:
    """Validate SDK config and basic completion via the reasoning model."""
    print(f"\nPHASE 2 — Basic chat ({REASONING_MODEL})")
    start = time.time()
    try:
        resp = client.chat.completions.create(
            model=REASONING_MODEL,
            messages=[{"role": "user", "content": "What is 2+2? Reply with just the number."}],
            max_tokens=16,
            temperature=0,
        )
        elapsed = int((time.time() - start) * 1000)
        content = resp.choices[0].message.content.strip()
        if "4" not in content:
            print(f"  FAIL — Unexpected response: {content!r}")
            return False
        print(f"  OK   — Response: {content!r}  ({elapsed}ms)")
        return True

    except Exception as exc:
        print(f"  FAIL — {exc}")
        logger.exception("Phase 2 failed")
        return False


# ---------------------------------------------------------------------------
# Phase 3 — Embedding call (mxbai-embed-large-v1)
# ---------------------------------------------------------------------------

def phase3_embedding(client: OpenAI) -> bool:
    """Validate embedding model returns a 1024-dim vector."""
    print(f"\nPHASE 3 — Embedding ({EMBEDDING_MODEL})")
    start = time.time()
    try:
        resp = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input="Software engineer with 5 years of Python experience",
        )
        elapsed = int((time.time() - start) * 1000)
        embedding = resp.data[0].embedding
        dims = len(embedding)
        if dims != EMBEDDING_DIMS:
            print(f"  WARN — Unexpected dims: {dims} (expected {EMBEDDING_DIMS})")
        else:
            print(f"  OK   — Embedding dims: {dims}  ({elapsed}ms)")
        # Check for non-zero vector
        if all(v == 0.0 for v in embedding[:10]):
            print("  FAIL — Zero vector returned")
            return False
        return True

    except Exception as exc:
        print(f"  FAIL — {exc}")
        logger.exception("Phase 3 failed")
        return False


# ---------------------------------------------------------------------------
# Phase 4 — Structured output via GPT extraction model
# ---------------------------------------------------------------------------

def phase4_structured_output(client: OpenAI) -> bool:
    """Validate json_schema structured output (GPT models only — Claude returns HTTP 500)."""
    print(f"\nPHASE 4 — Structured output ({EXTRACTION_MODEL})")
    start = time.time()
    try:
        resp = client.chat.completions.create(
            model=EXTRACTION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Extract required and desired skills from job descriptions.",
                },
                {
                    "role": "user",
                    "content": (
                        "Job: Senior Python Engineer. "
                        "Must have: Python, SQL. "
                        "Nice to have: Docker, Kubernetes."
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "skill_extraction",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "required_skills": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "desired_skills": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["required_skills", "desired_skills"],
                        "additionalProperties": False,
                    },
                },
            },
            temperature=0,
        )
        elapsed = int((time.time() - start) * 1000)
        import json
        parsed = json.loads(resp.choices[0].message.content)
        req = parsed.get("required_skills", [])
        des = parsed.get("desired_skills", [])
        print(f"  OK   — required={req}, desired={des}  ({elapsed}ms)")
        return True

    except Exception as exc:
        print(f"  FAIL — {exc}")
        logger.exception("Phase 4 failed")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    print("=" * 64)
    print("Genesis API Connectivity Test")
    print("=" * 64)
    print(f"Base URL : {GENESIS_BASE_URL}")
    print(f"Org      : {GENESIS_ORG}")
    print(f"SSL cert : {SSL_CERT}")

    try:
        api_key = _get_api_key()
    except EnvironmentError as exc:
        print(f"\nERROR: {exc}")
        return

    results: dict[str, bool] = {}

    results["raw_http"] = phase1_raw_http(api_key)
    if not results["raw_http"]:
        print("\nAborting — Phase 1 failed. Check network/auth before continuing.")
        _print_summary(results)
        return

    client = _make_client(api_key)

    results["basic_chat"] = phase2_basic_chat(client)
    results["embedding"] = phase3_embedding(client)
    results["structured_output"] = phase4_structured_output(client)

    _print_summary(results)


def _print_summary(results: dict[str, bool]) -> None:
    labels = {
        "raw_http": "Phase 1 — Raw HTTP",
        "basic_chat": "Phase 2 — Basic chat",
        "embedding": "Phase 3 — Embedding",
        "structured_output": "Phase 4 — Structured output",
    }
    print("\n" + "=" * 64)
    print("SUMMARY")
    print("=" * 64)
    all_pass = True
    for key, label in labels.items():
        status = results.get(key)
        if status is None:
            print(f"  SKIP  {label}")
        elif status:
            print(f"  PASS  {label}")
        else:
            print(f"  FAIL  {label}")
            all_pass = False

    if all_pass and len(results) == 4:
        print("\nAll phases passed — Genesis API is ready.")
    else:
        print("\nOne or more phases failed — see output above.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genesis API connectivity test")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    main(verbose=args.verbose)
