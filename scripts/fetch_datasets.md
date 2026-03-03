# Fetch Datasets (Small Samples Only)

## Goal
Fetch metadata and tiny sample slices only. Do not pull full dumps by default.

## Environment
```bash
export USAJOBS_USER_AGENT='your-email@example.com'
export USAJOBS_API_KEY='replace-with-key'
mkdir -p data/raw/usajobs/2026-03-03 data/raw/onet/2026-03-03 data/raw/census/2026-03-03
```

## USAJOBS Sample (25 rows)
```bash
curl -s 'https://data.usajobs.gov/api/search?ResultsPerPage=25&Page=1&Keyword=data%20engineer' \
  -H 'Host: data.usajobs.gov' \
  -H "User-Agent: ${USAJOBS_USER_AGENT}" \
  -H "Authorization-Key: ${USAJOBS_API_KEY}" \
  > data/raw/usajobs/2026-03-03/usajobs_sample_page1.json
```

## O*NET Metadata Snapshot
```bash
curl -L -o data/raw/onet/2026-03-03/onet_database_page.html \
  'https://www.onetcenter.org/database.html'
```

## Census Metadata Snapshot
```bash
curl -L -o data/raw/census/2026-03-03/acs_microdata_page.html \
  'https://www.census.gov/programs-surveys/acs/microdata.html'
```

## Checksums
```bash
shasum -a 256 data/raw/usajobs/2026-03-03/usajobs_sample_page1.json
shasum -a 256 data/raw/onet/2026-03-03/onet_database_page.html
shasum -a 256 data/raw/census/2026-03-03/acs_microdata_page.html
```

## Next Step
Populate `manifest.json` for each source drop following:
- [`docs/data-layers/raw/naming-and-manifests.md`](../docs/data-layers/raw/naming-and-manifests.md)
