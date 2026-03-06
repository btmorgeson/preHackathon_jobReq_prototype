"""
Phase 4: Neo4j bulk import.

Usage:
    python scripts/04_neo4j_import.py
    python scripts/04_neo4j_import.py --graph-export-dir data/exports/graph
    python scripts/04_neo4j_import.py --reuse-existing

Requires:
    - Docker running with container neo4j-prototype
    - CSVs generated in data/exports/graph/nodes and data/exports/graph/edges
"""

from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Neo4j bulk import pipeline")
    parser.add_argument(
        "--graph-export-dir",
        default="data/exports/graph",
        help="Directory containing nodes/ and edges/ CSV subdirectories.",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Skip import when graph data already exists in Neo4j.",
    )
    args = parser.parse_args()

    from src.pipeline.load.neo4j_setup import run_import

    logger.info("Starting Neo4j import from: %s", args.graph_export_dir)
    try:
        counts = run_import(
            graph_export_dir=args.graph_export_dir,
            overwrite_destination=not args.reuse_existing,
        )
    except RuntimeError as exc:
        logger.error("Import failed: %s", exc)
        sys.exit(1)

    print("\nImport complete. Node and relationship counts:")
    for name, count in counts.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
