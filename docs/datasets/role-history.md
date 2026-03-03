# Role History (Aggregate Career Proxies)

## Official US Sources
1. Census SIPP datasets
- Link: https://www.census.gov/programs-surveys/sipp/data/datasets.html
- Accessed: 2026-03-03
- Version: N/A

2. BLS time-series via API
- Link: https://www.bls.gov/developers/
- Accessed: 2026-03-03
- Version: Public Data API 2.0

3. OPM data portal and migration notes
- Links:
  - https://www.opm.gov/data/
  - https://www.opm.gov/data/datasets/
- Accessed: 2026-03-03
- Version: N/A

## How to Use in This Prototype
- Use time-series and aggregate transitions as role-history priors.
- Build `RoleHistoryAggregate` nodes keyed by period/occupation/agency/region.
- Join to postings and skill demand trends for context expansion.

## Explicit Limitation
- Person-level longitudinal employment trajectories are generally restricted or not available as open, directly linkable official datasets.
- This prototype therefore uses aggregate proxy history only.
