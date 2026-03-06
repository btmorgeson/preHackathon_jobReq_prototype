"""Orchestrate the full data->graph->embedding pipeline with quality checks."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.fetch.onet_fetcher import RAW_DIR, fetch_onet
from src.pipeline.load.graph_csv_builder import EDGES_DIR, NODES_DIR, PARQUET_DIR, build_all
from src.pipeline.load.neo4j_setup import run_import
from src.pipeline.quality_checks import (
    assert_generated_dataframes,
    assert_graph_csv_exports,
    assert_onet_payload,
)
from src.pipeline.transform.synthetic_employees import OUTPUT_DIR, generate
from src.pipeline.embed.embed_pipeline import run_embed_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = ["GENESIS_SKLZ_API_KEY", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]


def _step(name: str, fn):
    started = time.perf_counter()
    logger.info("==> %s", name)
    value = fn()
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("<== %s complete (%.2f ms)", name, elapsed_ms)
    return value, round(elapsed_ms, 2)


def _validate_env() -> None:
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Run scripts/validate_env.py --profile pipeline."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full prototype pipeline with checks.")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip O*NET fetch and use existing raw file.")
    parser.add_argument(
        "--reuse-existing-graph",
        action="store_true",
        help="Reuse existing Neo4j graph data if present.",
    )
    parser.add_argument(
        "--rebuild-embeddings",
        action="store_true",
        help="Rebuild all embeddings from scratch.",
    )
    parser.add_argument(
        "--rebuild-indexes",
        action="store_true",
        help="Drop/recreate vector indexes during embedding step.",
    )
    args = parser.parse_args()

    timings: dict[str, float] = {}
    _validate_env()

    if args.skip_fetch:
        onet_path = RAW_DIR / "onet_data.json"
        if not onet_path.exists():
            raise RuntimeError(f"{onet_path} not found. Run without --skip-fetch to generate it.")
        onet_data = json.loads(onet_path.read_text(encoding="utf-8"))
    else:
        onet_data, timings["fetch_onet_ms"] = _step("Fetch O*NET data", lambda: fetch_onet(RAW_DIR))
    assert_onet_payload(onet_data)

    dfs, timings["generate_data_ms"] = _step(
        "Generate synthetic people/postings",
        lambda: generate(onet_data, OUTPUT_DIR),
    )
    assert_generated_dataframes(dfs)

    _, timings["build_graph_csv_ms"] = _step(
        "Build graph CSV exports",
        lambda: build_all(PARQUET_DIR, NODES_DIR, EDGES_DIR),
    )
    assert_graph_csv_exports(Path("data/exports/graph"))

    counts, timings["neo4j_import_ms"] = _step(
        "Import graph into Neo4j",
        lambda: run_import(
            graph_export_dir="data/exports/graph",
            overwrite_destination=not args.reuse_existing_graph,
        ),
    )

    embed_result, timings["embed_ms"] = _step(
        "Generate embeddings and indexes",
        lambda: run_embed_pipeline(
            rebuild_embeddings=args.rebuild_embeddings,
            rebuild_indexes=args.rebuild_indexes,
        ),
    )

    print("\nPipeline complete.")
    print("Node/relationship counts:")
    for name, count in counts.items():
        print(f"  {name}: {count}")
    print("Embedding output:")
    print(f"  chunks_embedded: {embed_result['chunks_embedded']}")
    print(f"  roles_embedded : {embed_result['roles_embedded']}")
    print("Timing summary (ms):")
    for step_name, elapsed_ms in timings.items():
        print(f"  {step_name}: {elapsed_ms}")


if __name__ == "__main__":
    main()
