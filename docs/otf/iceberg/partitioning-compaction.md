# Partitioning and Compaction

## Partitioning Guidance
- Prefer transform partitions (`days(ts)`, `bucket(id, N)`) over high-cardinality identity partitions.
- Keep partition strategy aligned to dominant filters (date, region, agency, role family).

## File Sizing
- Inference: target ~128MB to ~512MB data files for balanced scan planning in most object-store analytics workflows.
- Reason: Iceberg docs describe planning/performance impact of file counts but do not prescribe one universal size.

## Compaction
- Schedule rewrite/compaction after many small writes.
- Evaluate rewrite actions in your chosen engine (Spark procedures or external maintenance jobs).

## Schema Evolution
- Additive column changes are generally safer than type narrowing.
- Preserve source fields and derived fields separately to avoid breaking backfills.

## Official Sources
- Performance: https://iceberg.apache.org/docs/latest/performance/ (Accessed: 2026-03-03, Version: 1.10.1 docs branch)
- Evolution: https://iceberg.apache.org/docs/latest/evolution/ (Accessed: 2026-03-03, Version: 1.10.1 docs branch)
