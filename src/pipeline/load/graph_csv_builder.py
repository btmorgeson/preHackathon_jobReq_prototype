"""
Graph CSV builder.

Reads Parquet files and emits Neo4j admin import CSVs with LF line endings.
Node and edge CSVs use QUOTE_ALL for safety.
"""

import csv
import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PARQUET_DIR = Path("data/parquet")
NODES_DIR = Path("data/exports/graph/nodes")
EDGES_DIR = Path("data/exports/graph/edges")


def _open_csv(path: Path) -> tuple:
    """Open a CSV file for writing with LF line endings and return (file, writer)."""
    f = open(path, "w", newline="\n", encoding="utf-8")
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    return f, writer


def build_node_csvs(parquet_dir: Path = PARQUET_DIR, nodes_dir: Path = NODES_DIR) -> None:
    """Build all node CSVs from Parquet files."""
    nodes_dir.mkdir(parents=True, exist_ok=True)

    # persons.csv
    persons_df = pd.read_parquet(parquet_dir / "persons.parquet")
    path = nodes_dir / "persons.csv"
    with _open_csv(path)[0] as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":ID(Person)", "stable_id", "name", "employee_id", "current_title", ":LABEL"])
        for _, row in persons_df.iterrows():
            w.writerow([row["stable_id"], row["stable_id"], row["name"], row["employee_id"], row["current_title"], "Person"])
    logger.info("Wrote persons.csv (%d rows)", len(persons_df))

    # roles.csv
    roles_df = pd.read_parquet(parquet_dir / "roles.parquet")
    path = nodes_dir / "roles.csv"
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":ID(Role)", "stable_id", "title", "soc_code", "start_date", "end_date", "is_current:boolean", ":LABEL"])
        for _, row in roles_df.iterrows():
            w.writerow([
                row["stable_id"],
                row["stable_id"],
                row["title"],
                row["soc_code"],
                row["start_date"] or "",
                row["end_date"] or "",
                str(row["is_current"]).lower(),
                "Role",
            ])
    logger.info("Wrote roles.csv (%d rows)", len(roles_df))

    # skills.csv
    skills_df = pd.read_parquet(parquet_dir / "skills.parquet")
    path = nodes_dir / "skills.csv"
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":ID(Skill)", "stable_id", "name", ":LABEL"])
        for _, row in skills_df.iterrows():
            w.writerow([row["stable_id"], row["stable_id"], row["name"], "Skill"])
    logger.info("Wrote skills.csv (%d rows)", len(skills_df))

    # chunks.csv
    chunks_df = pd.read_parquet(parquet_dir / "chunks.parquet")
    path = nodes_dir / "chunks.csv"
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":ID(Chunk)", "stable_id", "text", "chunk_type", ":LABEL"])
        for _, row in chunks_df.iterrows():
            w.writerow([row["stable_id"], row["stable_id"], row["text"], row["chunk_type"], "Chunk"])
    logger.info("Wrote chunks.csv (%d rows)", len(chunks_df))

    # postings.csv
    postings_df = pd.read_parquet(parquet_dir / "postings.parquet")
    path = nodes_dir / "postings.csv"
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":ID(Posting)", "stable_id", "req_number", "title", "description", ":LABEL"])
        for _, row in postings_df.iterrows():
            w.writerow([row["stable_id"], row["stable_id"], row["req_number"], row["title"], row["description"], "Posting"])
    logger.info("Wrote postings.csv (%d rows)", len(postings_df))


def build_edge_csvs(parquet_dir: Path = PARQUET_DIR, edges_dir: Path = EDGES_DIR) -> None:
    """Build all edge CSVs from Parquet files."""
    edges_dir.mkdir(parents=True, exist_ok=True)

    roles_df = pd.read_parquet(parquet_dir / "roles.parquet")
    person_skills_df = pd.read_parquet(parquet_dir / "person_skills.parquet")
    chunks_df = pd.read_parquet(parquet_dir / "chunks.parquet")
    postings_df = pd.read_parquet(parquet_dir / "postings.parquet")
    skills_df = pd.read_parquet(parquet_dir / "skills.parquet")

    # has_role.csv
    path = edges_dir / "has_role.csv"
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":START_ID(Person)", ":END_ID(Role)", ":TYPE"])
        for _, row in roles_df.iterrows():
            w.writerow([row["person_stable_id"], row["stable_id"], "HAS_ROLE"])
    logger.info("Wrote has_role.csv (%d rows)", len(roles_df))

    # has_skill.csv
    path = edges_dir / "has_skill.csv"
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":START_ID(Person)", ":END_ID(Skill)", ":TYPE"])
        for _, row in person_skills_df.iterrows():
            w.writerow([row["person_stable_id"], row["skill_stable_id"], "HAS_SKILL"])
    logger.info("Wrote has_skill.csv (%d rows)", len(person_skills_df))

    # has_chunk.csv
    path = edges_dir / "has_chunk.csv"
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":START_ID(Person)", ":END_ID(Chunk)", ":TYPE"])
        for _, row in chunks_df.iterrows():
            w.writerow([row["person_stable_id"], row["stable_id"], "HAS_CHUNK"])
    logger.info("Wrote has_chunk.csv (%d rows)", len(chunks_df))

    # requires_skill.csv — from postings required + desired skills
    skill_name_to_id = {row["name"]: row["stable_id"] for _, row in skills_df.iterrows()}
    path = edges_dir / "requires_skill.csv"
    edge_count = 0
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow([":START_ID(Posting)", ":END_ID(Skill)", "required:boolean", ":TYPE"])
        for _, row in postings_df.iterrows():
            posting_id = row["stable_id"]
            required_skills = list(row["required_skills"]) if row["required_skills"] is not None else []
            desired_skills = list(row["desired_skills"]) if row["desired_skills"] is not None else []
            for skill_name in required_skills:
                if skill_name in skill_name_to_id:
                    w.writerow([posting_id, skill_name_to_id[skill_name], "true", "REQUIRES_SKILL"])
                    edge_count += 1
            for skill_name in desired_skills:
                if skill_name in skill_name_to_id:
                    w.writerow([posting_id, skill_name_to_id[skill_name], "false", "REQUIRES_SKILL"])
                    edge_count += 1
    logger.info("Wrote requires_skill.csv (%d rows)", edge_count)


def build_all(
    parquet_dir: Path = PARQUET_DIR,
    nodes_dir: Path = NODES_DIR,
    edges_dir: Path = EDGES_DIR,
) -> None:
    """Build all node and edge CSVs."""
    build_node_csvs(parquet_dir, nodes_dir)
    build_edge_csvs(parquet_dir, edges_dir)
    logger.info("Graph CSV build complete.")
