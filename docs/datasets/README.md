# Datasets (US-only)

## Purpose
List official US datasets that can power a people/roles/skills/postings prototype graph without committing large raw dumps to git.

## What You'll Learn
- Which datasets map cleanly to each graph entity type.
- How to sample data safely for local prototyping.
- Where official licensing and use constraints apply.

## Prerequisites
- API keys where required (for example USAJOBS API key).
- `curl`, `jq`, and optional Python for sample extraction.
- Review [`licenses-and-ethics.md`](licenses-and-ethics.md) first.

## Quickstart
1. Read dataset shortlist in this folder.
2. Run only small-sample commands from [`/scripts/fetch_datasets.md`](../../scripts/fetch_datasets.md).
3. Save each raw sample with a manifest entry (checksum + source URL).
4. Normalize into canonical fields from [`schema-notes.md`](schema-notes.md).

## Deep Dive
- People/skills sources: [`people-and-skills.md`](people-and-skills.md)
- Posting text sources: [`job-postings-text.md`](job-postings-text.md)
- Role-history proxies: [`role-history.md`](role-history.md)
- Governance: [`licenses-and-ethics.md`](licenses-and-ethics.md)
- Schema strategy: [`schema-notes.md`](schema-notes.md)

## Common Mistakes / Gotchas
- Assuming person-level career histories are publicly available in official US datasets.
- Ignoring API terms and attribution requirements.
- Mixing SOC/O*NET occupational code systems without mapping tables.

## Official Sources
- O*NET Data: https://www.onetcenter.org/database.html (Accessed: 2026-03-03, Version: O*NET 30.0 shown)
- USAJOBS Developer API: https://developer.usajobs.gov/ (Accessed: 2026-03-03, Version: N/A)
- Census ACS PUMS: https://www.census.gov/programs-surveys/acs/microdata.html (Accessed: 2026-03-03, Version: N/A)
- Census SIPP datasets: https://www.census.gov/programs-surveys/sipp/data/datasets.html (Accessed: 2026-03-03, Version: N/A)
- BLS Developer API: https://www.bls.gov/developers/ (Accessed: 2026-03-03, Version: API v2 docs)
