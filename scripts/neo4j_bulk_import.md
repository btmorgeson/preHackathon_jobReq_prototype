# Neo4j Bulk Import Runbook

## Goal
Import generated graph CSV exports into Neo4j and apply baseline schema.

## Preconditions
- Graph CSV exports exist:
  - `data/exports/graph/nodes/*.csv`
  - `data/exports/graph/edges/*.csv`
- One Neo4j runtime is available:
  - Vagrant VM (primary): `vagrant up`
  - Docker container (alternate): `docker compose up -d neo4j`

## Standard Command (Vagrant / work machine default)
```bash
vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"
```

## Docker Alternate
```bash
python scripts/04_neo4j_import.py
```

## Reuse Existing Graph (Docker path only, skip destructive re-import)
```bash
python scripts/04_neo4j_import.py --reuse-existing
```

## Custom Export Directory (Docker path only)
```bash
python scripts/04_neo4j_import.py --graph-export-dir data/exports/graph
```

## Neo4j 5.26 Import CLI Note
- On Neo4j `5.26.x`, `neo4j-admin database import full` expects the database name as a positional argument.
- Correct pattern:
```bash
neo4j-admin database import full neo4j --overwrite-destination=true ...
```
- Avoid old flag form:
```bash
neo4j-admin database import full --database=neo4j ...
```

## Post-Import Checks
```bash
vagrant ssh -c "cypher-shell -u neo4j -p password12345 \"MATCH (p:Person) RETURN count(p) AS people;\""
vagrant ssh -c "cypher-shell -u neo4j -p password12345 \"MATCH (po:Posting) RETURN count(po) AS postings;\""
```

Docker equivalent:
```bash
docker exec -it neo4j-prototype cypher-shell -u neo4j -p password12345 "MATCH (p:Person) RETURN count(p) AS people;"
docker exec -it neo4j-prototype cypher-shell -u neo4j -p password12345 "MATCH (po:Posting) RETURN count(po) AS postings;"
```
