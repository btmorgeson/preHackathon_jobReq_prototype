#!/usr/bin/env bash
set -euo pipefail

GRAPH_EXPORT_DIR="${GRAPH_EXPORT_DIR:-/workspace/data/exports/graph}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-password12345}"

required_files=(
  "${GRAPH_EXPORT_DIR}/nodes/persons.csv"
  "${GRAPH_EXPORT_DIR}/nodes/roles.csv"
  "${GRAPH_EXPORT_DIR}/nodes/skills.csv"
  "${GRAPH_EXPORT_DIR}/nodes/chunks.csv"
  "${GRAPH_EXPORT_DIR}/nodes/postings.csv"
  "${GRAPH_EXPORT_DIR}/edges/has_role.csv"
  "${GRAPH_EXPORT_DIR}/edges/has_skill.csv"
  "${GRAPH_EXPORT_DIR}/edges/has_chunk.csv"
  "${GRAPH_EXPORT_DIR}/edges/requires_skill.csv"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing graph export file: $file"
    echo "Run python scripts/03_build_graph_csv.py on host before this import."
    exit 1
  fi
done

echo "Stopping Neo4j..."
sudo systemctl stop neo4j

echo "Removing previous neo4j database files..."
sudo rm -rf /var/lib/neo4j/data/databases/neo4j /var/lib/neo4j/data/transactions/neo4j

echo "Running offline neo4j-admin import..."
sudo -u neo4j neo4j-admin database import full \
  neo4j \
  --overwrite-destination=true \
  --nodes=Person="${GRAPH_EXPORT_DIR}/nodes/persons.csv" \
  --nodes=Role="${GRAPH_EXPORT_DIR}/nodes/roles.csv" \
  --nodes=Skill="${GRAPH_EXPORT_DIR}/nodes/skills.csv" \
  --nodes=Chunk="${GRAPH_EXPORT_DIR}/nodes/chunks.csv" \
  --nodes=Posting="${GRAPH_EXPORT_DIR}/nodes/postings.csv" \
  --relationships=HAS_ROLE="${GRAPH_EXPORT_DIR}/edges/has_role.csv" \
  --relationships=HAS_SKILL="${GRAPH_EXPORT_DIR}/edges/has_skill.csv" \
  --relationships=HAS_CHUNK="${GRAPH_EXPORT_DIR}/edges/has_chunk.csv" \
  --relationships=REQUIRES_SKILL="${GRAPH_EXPORT_DIR}/edges/requires_skill.csv"

echo "Starting Neo4j..."
sudo systemctl start neo4j

echo "Waiting for Neo4j..."
for _ in $(seq 1 60); do
  if curl -sSf http://localhost:7474 >/dev/null; then
    break
  fi
  sleep 2
done

echo "Applying constraints/indexes..."
queries=(
  "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.stable_id IS UNIQUE"
  "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE"
  "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.stable_id IS UNIQUE"
  "CREATE FULLTEXT INDEX skill_name_ft IF NOT EXISTS FOR (s:Skill) ON EACH [s.name]"
  "CREATE FULLTEXT INDEX role_title_ft IF NOT EXISTS FOR (r:Role) ON EACH [r.title]"
)

for query in "${queries[@]}"; do
  cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" "$query"
done

echo "Verifying graph counts..."
count_queries=(
  "MATCH (n:Person) RETURN count(n) AS Person"
  "MATCH (n:Role) RETURN count(n) AS Role"
  "MATCH (n:Skill) RETURN count(n) AS Skill"
  "MATCH (n:Chunk) RETURN count(n) AS Chunk"
  "MATCH (n:Posting) RETURN count(n) AS Posting"
  "MATCH ()-[r:HAS_ROLE]->() RETURN count(r) AS HAS_ROLE"
  "MATCH ()-[r:HAS_SKILL]->() RETURN count(r) AS HAS_SKILL"
  "MATCH ()-[r:HAS_CHUNK]->() RETURN count(r) AS HAS_CHUNK"
  "MATCH ()-[r:REQUIRES_SKILL]->() RETURN count(r) AS REQUIRES_SKILL"
)

for query in "${count_queries[@]}"; do
  cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" "$query"
done

echo "Fresh Neo4j graph import complete."
