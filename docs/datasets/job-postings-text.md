# Job Postings Text Datasets

## Primary Source
### USAJOBS API
- Link: https://developer.usajobs.gov/
- Accessed: 2026-03-03
- Version: N/A

## Why It Matters
- Provides official federal job posting text, qualification language, and metadata.
- Supports extracting skills/requirements from real posting descriptions for chunking and GraphRAG.

## Small-Sample Strategy
- Use search endpoint with narrow filters and low page counts.
- Save only sample JSON for prototyping, then convert to parquet.

Example sample command:
```bash
curl -s 'https://data.usajobs.gov/api/search?ResultsPerPage=25&Page=1&Keyword=data%20engineer' \
  -H 'Host: data.usajobs.gov' \
  -H "User-Agent: ${USAJOBS_USER_AGENT}" \
  -H "Authorization-Key: ${USAJOBS_API_KEY}" \
  > data/raw/usajobs_sample_page1.json
```

## Notes
- Respect USAJOBS API terms and headers from official docs.
- Keep full descriptions in lake storage; graph keeps references + chunk-level derivatives.
