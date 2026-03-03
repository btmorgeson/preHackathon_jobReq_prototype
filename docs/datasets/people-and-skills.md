# People and Skills Datasets

## Recommended Official Sources
1. O*NET Database and Web Services
- Role: occupation and skill taxonomy baseline.
- Links:
  - https://www.onetcenter.org/database.html
  - https://services.onetcenter.org/
- Accessed: 2026-03-03
- Version: O*NET Data 30.0 (page shows latest database release)

2. ACS PUMS (Census)
- Role: person/household microdata proxies (demographics, occupation codes, education), not direct skill labels.
- Link: https://www.census.gov/programs-surveys/acs/microdata.html
- Accessed: 2026-03-03
- Version: N/A (annual releases)

## Graph Contribution
- `Person` nodes: sampled synthetic or de-identified rows using source IDs from PUMS extract IDs.
- `Skill` nodes: seeded from O*NET skill and work activity dimensions.
- `HAS_ROLE` and `HAS_SKILL` relationships: created via mapping layer (inference from occupation codes).

## Person-Level Inference Boundary
- Inference: official US sources above do not provide direct person-skill ground truth at individual level; mapping from occupation to likely skills must be flagged as inferred.
