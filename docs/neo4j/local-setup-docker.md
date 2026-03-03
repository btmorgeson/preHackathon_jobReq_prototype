# Neo4j Local Setup (Docker)

## Compose Service
The root `docker-compose.yml` defines:
- Image: `neo4j:2026.01.4-community-ubi10`
- Ports: `7474` (HTTP), `7687` (Bolt)
- Volumes: `/data`, `/logs`, `/import`, `/plugins`
- Plugins: `apoc`, `genai`

## Start and Verify
```bash
docker compose up -d neo4j
curl -I http://localhost:7474
```

Optional check with Cypher shell:
```bash
docker exec -it neo4j-prototype cypher-shell -u neo4j -p password12345 "RETURN 1 AS ok;"
```

## Volume Strategy
- `neo4j_data`: database store and transaction logs.
- `neo4j_logs`: operational logs for troubleshooting.
- `neo4j_import`: CSV import mount for `neo4j-admin` operations.
- `neo4j_plugins`: APOC/GenAI jars installed by plugin loader.

## Health Checks
- Compose health check probes `http://localhost:7474`.
- Additional operational check:
  - `docker logs neo4j-prototype --tail 100`

## Platform Notes
- macOS and Linux: bind mounts and named volumes work as configured.
- Windows: prefer WSL2 + Docker Desktop; avoid editing CSVs in Excel before import to prevent delimiter/encoding drift.

## Inference Notes
- Inference: memory values in this file (2G heap, 1G page cache) are starter settings and should be tuned per host RAM and graph size.
