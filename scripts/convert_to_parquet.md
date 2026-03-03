# Convert to Parquet

## Goal
Transform raw sample datasets into deterministic parquet outputs.

## Directory Prep
```bash
mkdir -p data/parquet/usajobs data/parquet/onet
```

## USAJOBS JSON -> Parquet (DuckDB)
```bash
duckdb <<'SQL'
COPY (
  SELECT
    json_extract_string(item.value, '$.MatchedObjectId') AS source_id,
    json_extract_string(item.value, '$.MatchedObjectDescriptor.PositionTitle') AS title,
    json_extract_string(item.value, '$.MatchedObjectDescriptor.UserArea.Details.JobSummary') AS summary,
    'usajobs' AS source_system,
    '2026-03-03' AS version
  FROM read_json_auto('data/raw/usajobs/2026-03-03/usajobs_sample_page1.json') t,
       UNNEST(t.SearchResult.SearchResultItems) AS item
) TO 'data/parquet/usajobs/postings.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
SQL
```

## Validation
```bash
duckdb -c "SELECT count(*) FROM 'data/parquet/usajobs/postings.parquet';"
duckdb -c "DESCRIBE SELECT * FROM 'data/parquet/usajobs/postings.parquet';"
```

## Notes
- Keep IDs as strings.
- Keep `source_system`, `source_id`, `stable_id` fields present for downstream joins.
