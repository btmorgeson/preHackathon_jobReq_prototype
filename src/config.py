"""Centralized runtime configuration for API and pipeline modules."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


DEFAULT_SSL_CERT_PATH = "C:/Users/%USERNAME%/combined_pem.pem"


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped if stripped else default


def _split_csv(value: str | None, fallback: list[str]) -> list[str]:
    if not value:
        return fallback
    values = [item.strip() for item in value.split(",")]
    return [item for item in values if item]


@dataclass(frozen=True)
class Settings:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    ssl_cert_file: str
    genesis_api_key: str | None
    genesis_base_url: str
    genesis_org: str
    genesis_reasoning_model: str
    genesis_extraction_model: str
    genesis_embedding_model: str
    cors_allow_origins: list[str]
    default_top_k: int
    max_top_k: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    ssl_cert_value = _get_env("SSL_CERT_FILE", DEFAULT_SSL_CERT_PATH) or DEFAULT_SSL_CERT_PATH
    ssl_cert_file = os.path.expandvars(ssl_cert_value)
    os.environ.setdefault("SSL_CERT_FILE", ssl_cert_file)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ssl_cert_file)

    return Settings(
        neo4j_uri=_get_env("NEO4J_URI", "bolt://localhost:7687") or "bolt://localhost:7687",
        neo4j_user=_get_env("NEO4J_USER", "neo4j") or "neo4j",
        neo4j_password=_get_env("NEO4J_PASSWORD", "password12345") or "password12345",
        ssl_cert_file=ssl_cert_file,
        genesis_api_key=_get_env("GENESIS_SKLZ_API_KEY"),
        genesis_base_url=_get_env("GENESIS_BASE_URL", "https://api.ai.us.lmco.com/v1")
        or "https://api.ai.us.lmco.com/v1",
        genesis_org=_get_env("GENESIS_ORG", "SKLZ") or "SKLZ",
        genesis_reasoning_model=_get_env(
            "GENESIS_REASONING_MODEL",
            "claude-4-5-sonnet-latest",
        )
        or "claude-4-5-sonnet-latest",
        genesis_extraction_model=_get_env("GENESIS_EXTRACTION_MODEL", "gpt-oss-120b")
        or "gpt-oss-120b",
        genesis_embedding_model=_get_env("GENESIS_EMBEDDING_MODEL", "mxbai-embed-large-v1")
        or "mxbai-embed-large-v1",
        cors_allow_origins=_split_csv(
            _get_env("CORS_ALLOW_ORIGINS"),
            ["http://localhost:3000", "http://localhost:3001"],
        ),
        default_top_k=int(_get_env("SEARCH_DEFAULT_TOP_K", "10") or 10),
        max_top_k=int(_get_env("SEARCH_MAX_TOP_K", "50") or 50),
    )
