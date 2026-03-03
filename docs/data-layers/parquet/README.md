# Parquet Layer

## Purpose
Standardize transformed datasets into columnar parquet files for efficient analytical processing and Iceberg table creation.

## What You'll Learn
- Why parquet is preferred over raw CSV/JSON for this stage.
- Partitioning and file-size targets for local + scalable runs.
- How to avoid schema and null-type pitfalls.

## Prerequisites
- Raw sample files and manifests.
- DuckDB or PyArrow.

## Quickstart
1. Follow [`conversion-guide.md`](conversion-guide.md).
2. Write parquet outputs into `data/parquet/<dataset_id>/`.
3. Keep row-group/file-size in practical ranges (see below).

## Deep Dive
- Conversion recipes and caveats: [`conversion-guide.md`](conversion-guide.md)
- Iceberg integration path: [`/Users/brandonmorgeson/Documents/dev/preHackathon_jobReq_prototype/docs/otf/iceberg/write-read-examples.md`](../../otf/iceberg/write-read-examples.md)

## Common Mistakes / Gotchas
- Writing many tiny parquet files (small-file problem).
- Letting schema drift across partitions.
- Losing `source_id`/`stable_id` fields during projection.

## Official Sources
- Apache Iceberg performance guidance (file sizing and planning implications): https://iceberg.apache.org/docs/latest/performance/ (Accessed: 2026-03-03, Version: 1.10.1 docs branch)
- Apache Parquet format reference: https://parquet.apache.org/docs/ (Accessed: 2026-03-03, Version: current site)
