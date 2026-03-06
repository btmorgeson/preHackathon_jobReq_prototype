"""Reusable data-quality checks for pipeline stages."""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


def assert_onet_payload(onet_data: dict) -> None:
    occupations = onet_data.get("occupations", [])
    all_skills = onet_data.get("all_skills", [])
    all_activities = onet_data.get("all_activities", [])
    if not occupations:
        raise ValueError("O*NET payload has no occupations.")
    if not all_skills:
        raise ValueError("O*NET payload has no skills.")
    if not all_activities:
        raise ValueError("O*NET payload has no activities.")


def assert_generated_dataframes(dfs: dict[str, pd.DataFrame]) -> None:
    required_frames = ["persons", "roles", "skills", "person_skills", "chunks", "postings"]
    for frame_name in required_frames:
        if frame_name not in dfs:
            raise ValueError(f"Missing expected dataframe: {frame_name}")
        if dfs[frame_name].empty:
            raise ValueError(f"Generated dataframe is empty: {frame_name}")

    persons = dfs["persons"]
    if persons["stable_id"].nunique() != len(persons):
        raise ValueError("Person stable_id values are not unique.")

    person_ids = set(persons["stable_id"].tolist())
    roles = dfs["roles"]
    role_person_ids = set(roles["person_stable_id"].tolist())
    if not role_person_ids.issubset(person_ids):
        raise ValueError("Role rows reference unknown person_stable_id values.")

    chunks = dfs["chunks"]
    chunk_person_ids = set(chunks["person_stable_id"].tolist())
    if not chunk_person_ids.issubset(person_ids):
        raise ValueError("Chunk rows reference unknown person_stable_id values.")


def assert_graph_csv_exports(export_dir: Path) -> None:
    expected = [
        export_dir / "nodes" / "persons.csv",
        export_dir / "nodes" / "roles.csv",
        export_dir / "nodes" / "skills.csv",
        export_dir / "nodes" / "chunks.csv",
        export_dir / "nodes" / "postings.csv",
        export_dir / "edges" / "has_role.csv",
        export_dir / "edges" / "has_skill.csv",
        export_dir / "edges" / "has_chunk.csv",
        export_dir / "edges" / "requires_skill.csv",
    ]
    for file_path in expected:
        if not file_path.exists():
            raise ValueError(f"Missing graph export file: {file_path}")
        with open(file_path, encoding="utf-8") as handle:
            reader = csv.reader(handle)
            try:
                next(reader)  # header
            except StopIteration as exc:
                raise ValueError(f"Graph export file is empty: {file_path}") from exc
            try:
                next(reader)
            except StopIteration as exc:
                raise ValueError(f"Graph export file has no data rows: {file_path}") from exc
