# Raw Naming and Manifests

## Folder Naming
Use:
```text
data/raw/<dataset_id>/<YYYY-MM-DD>/<file>
```

Example:
```text
data/raw/usajobs/2026-03-03/usajobs_sample_page1.json
```

## `manifest.json` Contract
Each raw drop directory should include a `manifest.json` array using this schema:

```json
[
  {
    "dataset_id": "usajobs",
    "source_url": "https://data.usajobs.gov/api/search?ResultsPerPage=25&Page=1&Keyword=data%20engineer",
    "license": "USAJOBS API terms",
    "retrieved_at": "2026-03-03T16:35:00Z",
    "sha256": "9fd5...",
    "record_count": 25,
    "schema_version": "v1",
    "lineage_parent": null,
    "notes": "Sample page for local prototype only"
  }
]
```

## Manifest Rules
- `dataset_id`: stable short identifier.
- `source_url`: exact retrieval endpoint or file URL.
- `schema_version`: version of normalization mapping expected downstream.
- `lineage_parent`: source artifact ID when file is derived from another raw asset.
- `notes`: include redaction status and sampling constraints.
