"""
Phase 5: Embed Chunk and Role nodes, then ensure vector indexes.

Usage:
    python scripts/05_embed_chunks.py
    python scripts/05_embed_chunks.py --rebuild-embeddings
    python scripts/05_embed_chunks.py --rebuild-indexes
    python scripts/05_embed_chunks.py --rebuild-mentions

Requires:
    - GENESIS_SKLZ_API_KEY set in environment
    - Neo4j container running and data already imported (run 04_neo4j_import.py first)
"""

from __future__ import annotations

import argparse
import logging
import sys

from src.pipeline.embed.embed_pipeline import run_embed_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed chunks/roles and manage vector indexes.")
    parser.add_argument(
        "--rebuild-embeddings",
        action="store_true",
        help="Drop all existing embeddings and rebuild from scratch.",
    )
    parser.add_argument(
        "--rebuild-indexes",
        action="store_true",
        help="Drop existing vector indexes and recreate them.",
    )
    parser.add_argument(
        "--rebuild-mentions",
        action="store_true",
        help="Drop existing MENTIONS edges and relink from scratch.",
    )
    args = parser.parse_args()

    logger.info("Starting embedding pipeline...")
    try:
        result = run_embed_pipeline(
            rebuild_embeddings=args.rebuild_embeddings,
            rebuild_indexes=args.rebuild_indexes,
            rebuild_mentions=args.rebuild_mentions,
        )
    except Exception as exc:
        logger.error("Embed pipeline failed: %s", exc)
        sys.exit(1)

    print("\nEmbedding pipeline complete.")
    print(f"  Chunks embedded : {result['chunks_embedded']}")
    print(f"  Roles embedded  : {result['roles_embedded']}")
    print(f"  Mentions linked : {result['mentions_linked']}")
    print("  Vector indexes  :")
    for index_name in result["indexes"]:
        print(f"    - {index_name}")


if __name__ == "__main__":
    main()
