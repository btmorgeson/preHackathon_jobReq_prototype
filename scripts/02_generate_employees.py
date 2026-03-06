"""
CLI: Generate synthetic employees from O*NET data.

Reads data/raw/onet/onet_data.json (run 01_fetch_onet.py first),
then generates persons, roles, skills, chunks, and postings → data/parquet/.

Usage:
    python scripts/02_generate_employees.py
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.transform.synthetic_employees import OUTPUT_DIR, generate
from src.pipeline.quality_checks import assert_generated_dataframes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    onet_json = Path("data/raw/onet/onet_data.json")
    if not onet_json.exists():
        logger.error("O*NET data not found at %s. Run scripts/01_fetch_onet.py first.", onet_json)
        sys.exit(1)

    with open(onet_json, encoding="utf-8") as f:
        onet_data = json.load(f)

    logger.info("Generating synthetic employees...")
    dfs = generate(onet_data, OUTPUT_DIR)
    assert_generated_dataframes(dfs)

    print("\nSynthetic data generation complete:")
    for name, df in dfs.items():
        print(f"  {name:<20} {len(df):>6} rows  ->  data/parquet/{name}.parquet")

    persons_df = dfs["persons"]
    chunks_df = dfs["chunks"]
    print(f"\nValidation passed:")
    print(f"  Persons        : {len(persons_df)} (expected 500)")
    print(f"  Unique IDs     : {persons_df['stable_id'].nunique()}")
    print(f"  Chunks         : {len(chunks_df)} (expected >= 500)")


if __name__ == "__main__":
    main()
