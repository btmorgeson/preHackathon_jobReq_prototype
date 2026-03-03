# Large Text Best Practices

## Purpose
Define how to store and govern large text corpora so graph workloads remain efficient and traceable.

## What You'll Learn
- Why lake/object storage should hold raw text as system of record.
- How graph nodes should reference text instead of duplicating large payloads.
- How to maintain lineage across raw/parquet/iceberg/graph layers.

## Prerequisites
- `doc_id` and `source_uri` conventions defined in your schema.
- Raw layer manifest discipline.

## Quickstart
1. Keep full source text in raw/lake storage.
2. Store references (`doc_id`, `source_uri`) on `Document` and `Chunk` nodes.
3. Move only retrieval-critical text fragments into chunk nodes.
4. Apply versioning strategy from [`versioning-and-lineage.md`](versioning-and-lineage.md).

## Deep Dive
- Storage architecture patterns: [`storage-patterns.md`](storage-patterns.md)
- Version/lineage controls: [`versioning-and-lineage.md`](versioning-and-lineage.md)

## Common Mistakes / Gotchas
- Copying full raw document bodies into multiple graph nodes.
- Losing source URI + checksum traceability when reprocessing.
- Not tagging chunk extraction version after parser changes.

## Official Sources
- NIST Privacy Framework: https://www.nist.gov/privacy-framework (Accessed: 2026-03-03, Version: 1.1)
- NIST SP 800-122: https://csrc.nist.gov/pubs/sp/800/122/final (Accessed: 2026-03-03, Version: Final)
- Iceberg reliability: https://iceberg.apache.org/docs/latest/reliability/ (Accessed: 2026-03-03, Version: 1.10.1 docs branch)
