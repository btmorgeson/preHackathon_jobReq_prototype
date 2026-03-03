# Export Graph CSV

## Goal
Create deterministic node/edge CSV outputs for Neo4j bulk import.

## Example Export (DuckDB from Parquet)
```bash
mkdir -p data/exports/graph

duckdb <<'SQL'
COPY (
  SELECT
    stable_id AS postingId,
    title,
    source_system,
    source_id,
    stable_id,
    version,
    'Posting' AS label
  FROM 'data/parquet/usajobs/postings.parquet'
) TO 'data/exports/graph/posting.csv' (HEADER, DELIMITER ',');
SQL
```

## Header Files
Create matching headers:
```bash
cat > data/exports/graph/posting_header.csv <<'CSV'
postingId:ID(Posting),title:string,source_system:string,source_id:string,stable_id:string,version:string,:LABEL
CSV
```

## Deterministic IDs
- Use `stable_id = sha256(source_system|source_id|version)`.
- Recompute consistently in every run.

## Validation
```bash
wc -l data/exports/graph/posting.csv
head -n 5 data/exports/graph/posting.csv
```
