# Raw Layer

## Purpose
Define immutable ingestion rules for source datasets before transformation.

## What You'll Learn
- Raw layer immutability and lineage rules.
- How manifests and checksums provide reproducibility.
- How to structure raw paths for multi-source ingestion.

## Prerequisites
- Dataset source URLs and API credentials where required.
- A checksum utility (`sha256sum` or `shasum -a 256`).

## Quickstart
1. Place downloaded sample file in `data/raw/<dataset>/<date>/`.
2. Compute checksum.
3. Add entry to manifest using template from [`naming-and-manifests.md`](naming-and-manifests.md).
4. Never modify the raw file; publish corrections as new versioned drops.

## Deep Dive
- Naming conventions and manifest schema: [`naming-and-manifests.md`](naming-and-manifests.md)
- Storage policy: [`/Users/brandonmorgeson/Documents/dev/preHackathon_jobReq_prototype/data/README.md`](../../../data/README.md)

## Common Mistakes / Gotchas
- Editing raw JSON/CSV files in place.
- Missing checksum or source URL in manifest records.
- Reusing source IDs across different source systems without namespacing.

## Official Sources
- Data lineage concept in Iceberg docs: https://iceberg.apache.org/docs/latest/reliability/ (Accessed: 2026-03-03, Version: 1.10.1 docs branch)
- NIST guidance for data governance context: https://www.nist.gov/privacy-framework (Accessed: 2026-03-03, Version: 1.1)
