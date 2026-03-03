# Dataset Schema Notes

## Canonical Fields
All ingested entities should carry:
- `source_system`
- `source_id`
- `stable_id`
- `version`
- `ingested_at`

## Normalization Rules
- Occupation codes:
  - Preserve native coding system (`soc_code`, `onet_code`) in separate columns.
  - Maintain mapping table for SOC <-> O*NET when required.
- Dates:
  - Normalize to ISO 8601 UTC (`YYYY-MM-DD` or full timestamp).
- Text:
  - Store original text in lake storage with immutable `doc_id`.
  - Graph stores chunk text only where needed for retrieval.

## ID Strategy
- `stable_id` pattern:
  - `sha256(source_system + '|' + source_id + '|' + version)`
- Avoid random UUIDs for deterministic replay workflows.

## Inference Flags
- `is_inferred` boolean for edges/attributes derived from mappings (for example occupation -> likely skill).
- `inference_method` and `inference_version` fields for auditable transformations.
