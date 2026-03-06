# Export Graph CSV

## Goal
Create deterministic Neo4j import CSVs from generated Parquet data.

## Standard Command
```bash
python scripts/03_build_graph_csv.py
```

## Output Layout
- `data/exports/graph/nodes/`
  - `persons.csv`
  - `roles.csv`
  - `skills.csv`
  - `chunks.csv`
  - `postings.csv`
- `data/exports/graph/edges/`
  - `has_role.csv`
  - `has_skill.csv`
  - `has_chunk.csv`
  - `requires_skill.csv`

## Validation
`scripts/03_build_graph_csv.py` already verifies:
- all expected files exist
- each file has at least one row
- LF line endings are used (required by import tooling)
