"""Validate required environment variables for API and pipeline commands."""

from __future__ import annotations

import argparse
import os
import sys

PROFILES: dict[str, list[str]] = {
    "api": ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "GENESIS_SKLZ_API_KEY"],
    "pipeline": ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "GENESIS_SKLZ_API_KEY"],
    "frontend": ["NEXT_PUBLIC_API_URL"],
}

OPTIONAL_HINTS: dict[str, str] = {
    "SSL_CERT_FILE": "Set this when your environment requires a custom CA bundle.",
}


def _is_set(name: str) -> bool:
    value = os.environ.get(name)
    return bool(value and value.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate environment variables.")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        default="api",
        help="Validation profile to check.",
    )
    args = parser.parse_args()

    required = PROFILES[args.profile]
    missing = [name for name in required if not _is_set(name)]
    if missing:
        print(f"Environment validation failed for profile '{args.profile}'.")
        print("Missing required variables:")
        for name in missing:
            print(f"  - {name}")
        print("\nSet variables in your shell or .env source before running this command.")
        sys.exit(1)

    print(f"Environment validation passed for profile '{args.profile}'.")
    for hint_name, hint in OPTIONAL_HINTS.items():
        if not _is_set(hint_name):
            print(f"Note: {hint_name} not set. {hint}")


if __name__ == "__main__":
    main()
