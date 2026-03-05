"""
CLI: Fetch O*NET data and save to data/raw/onet/.

Usage:
    python scripts/01_fetch_onet.py
"""

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.fetch.onet_fetcher import RAW_DIR, fetch_onet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting O*NET fetch...")
    data = fetch_onet(RAW_DIR)
    occ_count = len(data["occupations"])
    skill_count = len(data["all_skills"])
    act_count = len(data["all_activities"])
    logger.info(
        "Done. occupations=%d  skills=%d  activities=%d",
        occ_count,
        skill_count,
        act_count,
    )
    print(f"\nO*NET fetch complete:")
    print(f"  Occupations : {occ_count}")
    print(f"  Skills      : {skill_count}")
    print(f"  Activities  : {act_count}")
    print(f"  Output      : {RAW_DIR / 'onet_data.json'}")


if __name__ == "__main__":
    main()
