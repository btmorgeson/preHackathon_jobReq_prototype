"""
Phase 4: Neo4j bulk import.

Usage:
    python scripts/04_neo4j_import.py [--data-dir data]

Requires:
    - Docker running with container neo4j-prototype
    - CSVs already generated in data/nodes/ and data/edges/
"""
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
        "--data-dir",
        default="data",
        help="Directory containing nodes/ and edges/ CSV subdirectories (default: data)",
    )
    args = parser.parse_args()

    from src.pipeline.load.neo4j_setup import run_import

    logger.info("Starting Neo4j import from: %s", args.data_dir)
    try:
        counts = run_import(data_dir=args.data_dir)
    except RuntimeError as exc:
        logger.error("Import failed: %s", exc)
        sys.exit(1)

    print("\nImport complete. Node and relationship counts:")
    for name, count in counts.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
