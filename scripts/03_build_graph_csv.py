"""
CLI: Build Neo4j admin import CSVs from Parquet files.

Reads data/parquet/*.parquet and writes CSVs to:
  data/exports/graph/nodes/  (5 node files)
  data/exports/graph/edges/  (4 edge files)

Usage:
    python scripts/03_build_graph_csv.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.load.graph_csv_builder import (
    EDGES_DIR,
    NODES_DIR,
    PARQUET_DIR,
    build_all,
)
from src.pipeline.quality_checks import assert_graph_csv_exports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

EXPECTED_FILES = [
    NODES_DIR / "persons.csv",
    NODES_DIR / "roles.csv",
    NODES_DIR / "skills.csv",
    NODES_DIR / "chunks.csv",
    NODES_DIR / "postings.csv",
    EDGES_DIR / "has_role.csv",
    EDGES_DIR / "has_skill.csv",
    EDGES_DIR / "has_chunk.csv",
    EDGES_DIR / "requires_skill.csv",
]


def _check_no_crlf(path: Path) -> bool:
    with open(path, "rb") as f:
        content = f.read()
    return b"\r\n" not in content


def main() -> None:
    build_all(PARQUET_DIR, NODES_DIR, EDGES_DIR)
    assert_graph_csv_exports(Path("data/exports/graph"))

    print("\nVerifying output files:")
    all_ok = True
    for path in EXPECTED_FILES:
        if not path.exists():
            print(f"  MISSING: {path}")
            all_ok = False
            continue
        has_crlf = not _check_no_crlf(path)
        rows = sum(1 for _ in open(path, encoding="utf-8")) - 1  # subtract header
        crlf_label = " [CRLF!]" if has_crlf else ""
        print(f"  OK  {path.name:<30}  {rows:>6} rows{crlf_label}")
        if has_crlf:
            all_ok = False

    if all_ok:
        print("\nAll 9 CSV files OK, LF line endings confirmed.")
    else:
        print("\nWARNING: Some files have issues — see above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
