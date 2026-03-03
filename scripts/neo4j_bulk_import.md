# Neo4j Bulk Import Runbook

## Goal
Import graph CSV exports into Neo4j and apply baseline schema.

## Preconditions
- `data/exports/graph/*.csv` and header files exist.
- Files copied into Neo4j import volume path.

## Copy into Import Volume
```bash
docker compose up -d neo4j

docker cp data/exports/graph/. neo4j-prototype:/import/
```

## Offline Import
```bash
docker compose stop neo4j

docker run --rm \
  -v neo4j_data:/data \
  -v neo4j_import:/import \
  neo4j:2026.01.4-community-ubi10 \
  neo4j-admin database import full \
  --overwrite-destination=true \
  --nodes=Posting=/import/posting_header.csv,/import/posting.csv \
  neo4j

docker compose start neo4j
```

## Post-Import Checks
```bash
docker exec -it neo4j-prototype cypher-shell -u neo4j -p password12345 \
  "MATCH (p:Posting) RETURN count(p) AS postings;"
```

## Rollback
- Stop container.
- Remove and recreate `neo4j_data` volume.
- Re-run import from known-good exports.
