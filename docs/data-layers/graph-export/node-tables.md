# Node Table Specifications

## Required Node Types
- `Person`
- `Role`
- `Skill`
- `Posting`
- `Chunk`
- `Document` (optional but recommended for provenance)

## Common Required Columns
- `source_system`
- `source_id`
- `stable_id`
- `version`

## Example: `Person`
```csv
personId:ID(Person),fullName,source_system,source_id,stable_id,version,:LABEL
p_001,Jane Doe,pums,12345,abc123,2026-03-03,Person
```

## Example: `Chunk`
```csv
chunkId:ID(Chunk),doc_id,text,token_count,start_offset,end_offset,embedding_model,embedding_dim,embedding_version,created_at,:LABEL
c_001,d_001,"Example chunk",220,0,912,text-embedding-3-large,3072,emb-v1,2026-03-03T17:00:00Z,Chunk
```
