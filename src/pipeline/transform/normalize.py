"""Stable ID generation for graph nodes."""

import hashlib


def make_stable_id(source: str, source_id: str, version: str = "v1") -> str:
    """Return a 16-char hex stable ID derived from source + source_id + version."""
    raw = f"{source}|{source_id}|{version}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
