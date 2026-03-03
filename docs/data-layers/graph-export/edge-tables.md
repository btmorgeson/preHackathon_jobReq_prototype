# Edge Table Specifications

## Relationship Types
- `HAS_ROLE` (`Person` -> `Role`)
- `REQUIRES_SKILL` (`Role|Posting` -> `Skill`)
- `MENTIONS` (`Chunk` -> `Skill|Role|Org|Posting`)
- `DERIVED_FROM` (`Posting|Chunk` -> `Document`)

## Required Relationship Columns
- `:START_ID(<Group>)`
- `:END_ID(<Group>)`
- `:TYPE`
- Provenance columns: `source_system`, `extractor_version`, `confidence`, `is_inferred`

## Example
```csv
:START_ID(Chunk),:END_ID(Skill),source_system,extractor_version,confidence,is_inferred,:TYPE
c_001,s_101,usajobs,nlp-v1,0.88,true,MENTIONS
```
