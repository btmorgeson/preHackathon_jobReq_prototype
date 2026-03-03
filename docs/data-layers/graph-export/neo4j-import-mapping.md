# Neo4j Import Mapping

## Header/File Naming
- Node headers: `<entity>_header.csv`
- Node data: `<entity>.csv`
- Relationship headers: `<relationship>_header.csv`
- Relationship data: `<relationship>.csv`

## Mapping Table
| Graph CSV | Neo4j Header Syntax |
|---|---|
| `Person` | `personId:ID(Person),..., :LABEL` |
| `Skill` | `skillId:ID(Skill),..., :LABEL` |
| `HAS_ROLE` | `:START_ID(Person),:END_ID(Role),..., :TYPE` |
| `MENTIONS` | `:START_ID(Chunk),:END_ID(Skill),..., :TYPE` |

## Import Assumptions
- Delimiter: comma
- Quote: double quote
- Array delimiter: semicolon
- ID type: string-based IDs (not integers)

## Null Handling
- Emit empty strings for optional text fields.
- Avoid literal `NULL` unless parser behavior is explicitly tested in your import pipeline.

## Reference Command
See [`/Users/brandonmorgeson/Documents/dev/preHackathon_jobReq_prototype/docs/neo4j/csv-import-bulk.md`](../../neo4j/csv-import-bulk.md).
