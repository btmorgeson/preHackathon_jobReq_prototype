# Conversion Guide: CSV/JSON -> Parquet

## Recipe A: DuckDB
```bash
mkdir -p data/parquet/usajobs

duckdb <<'SQL'
COPY (
  SELECT
    json_extract_string(j.value, '$.MatchedObjectId') AS source_id,
    json_extract_string(j.value, '$.MatchedObjectDescriptor.PositionTitle') AS title,
    json_extract_string(j.value, '$.MatchedObjectDescriptor.UserArea.Details.JobSummary') AS summary,
    'usajobs' AS source_system,
    '2026-03-03' AS version
  FROM read_json_auto('data/raw/usajobs/2026-03-03/usajobs_sample_page1.json') t,
       UNNEST(t.SearchResult.SearchResultItems) AS j
) TO 'data/parquet/usajobs/postings.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
SQL
```

## Recipe B: PyArrow
```bash
python - <<'PY'
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

df = pd.read_csv('data/raw/onet/2026-03-03/skills_sample.csv')
# Ensure stable column names and explicit types.
df['source_system'] = 'onet'
df['version'] = '2026-03-03'
table = pa.Table.from_pandas(df, preserve_index=False)
pq.write_table(table, 'data/parquet/onet/skills.parquet', compression='zstd')
PY
```

## Pitfalls
- Explicitly cast IDs as strings to prevent numeric truncation.
- Normalize text encoding to UTF-8 before writing.
- Store null-safe defaults for optional fields.
