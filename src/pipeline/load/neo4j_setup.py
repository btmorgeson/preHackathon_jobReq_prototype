"""
Neo4j bulk import and schema setup.

Steps:
1. Find Docker binary
2. docker cp all node and edge CSVs into container /import/
3. Stop Neo4j container
4. Run neo4j-admin database import full
5. Start container; poll health endpoint up to 60s
6. Apply constraints and indexes
7. Verify and log node/rel counts
"""
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

CONTAINER_NAME = "neo4j-prototype"
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password12345")
HEALTH_URL = "http://localhost:7474"
HEALTH_TIMEOUT_S = 60

NODE_CSVS = [
    ("Person", "nodes/persons.csv"),
    ("Role", "nodes/roles.csv"),
    ("Skill", "nodes/skills.csv"),
    ("Chunk", "nodes/chunks.csv"),
    ("Posting", "nodes/postings.csv"),
]

EDGE_CSVS = [
    ("HAS_ROLE", "edges/has_role.csv"),
    ("HAS_SKILL", "edges/has_skill.csv"),
    ("HAS_CHUNK", "edges/has_chunk.csv"),
    ("REQUIRES_SKILL", "edges/requires_skill.csv"),
]

CONSTRAINTS = [
    "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.stable_id IS UNIQUE",
    "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.stable_id IS UNIQUE",
    "CREATE FULLTEXT INDEX skill_name_ft IF NOT EXISTS FOR (s:Skill) ON EACH [s.name]",
    "CREATE FULLTEXT INDEX role_title_ft IF NOT EXISTS FOR (r:Role) ON EACH [r.title]",
]


def _find_docker() -> str:
    docker = shutil.which("docker")
    if docker:
        return docker
    fallback = "/usr/bin/docker"
    if os.path.isfile(fallback):
        return fallback
    raise RuntimeError("Docker binary not found in PATH or /usr/bin/docker")


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    logger.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def _copy_csvs(docker: str, data_dir: Path) -> None:
    """docker cp all node and edge CSVs into container /import/."""
    all_csvs = [(label, rel_path) for label, rel_path in NODE_CSVS + EDGE_CSVS]
    for _label, rel_path in all_csvs:
        local_path = data_dir / rel_path
        if not local_path.exists():
            raise RuntimeError(f"CSV not found: {local_path}")
        container_dir = f"{CONTAINER_NAME}:/import/{Path(rel_path).parent}"
        _run([docker, "exec", CONTAINER_NAME, "mkdir", "-p", f"/import/{Path(rel_path).parent}"])
        _run([docker, "cp", str(local_path), f"{CONTAINER_NAME}:/import/{rel_path}"])
        logger.info("Copied %s -> container:/import/%s", local_path.name, rel_path)


def _stop_container(docker: str) -> None:
    logger.info("Stopping container %s...", CONTAINER_NAME)
    _run([docker, "stop", CONTAINER_NAME])


def _import_database(docker: str) -> None:
    """Run neo4j-admin database import full."""
    node_args = [
        f"--nodes={label}=/import/{rel_path}"
        for label, rel_path in NODE_CSVS
    ]
    rel_args = [
        f"--relationships={label}=/import/{rel_path}"
        for label, rel_path in EDGE_CSVS
    ]
    cmd = [
        docker, "exec", CONTAINER_NAME,
        "neo4j-admin", "database", "import", "full",
        "--database=neo4j",
        "--overwrite-destination=true",
        *node_args,
        *rel_args,
    ]
    logger.info("Running neo4j-admin import (this may take a moment)...")
    _run(cmd)
    logger.info("Import complete.")


def _start_container(docker: str) -> None:
    logger.info("Starting container %s...", CONTAINER_NAME)
    _run([docker, "start", CONTAINER_NAME])


def _wait_for_health() -> None:
    """Poll Neo4j HTTP health endpoint until ready or timeout."""
    ssl_cert = os.environ.get("SSL_CERT_FILE", "C:/Users/e477258/combined_pem.pem")
    deadline = time.time() + HEALTH_TIMEOUT_S
    logger.info("Waiting for Neo4j to become healthy at %s...", HEALTH_URL)
    while time.time() < deadline:
        try:
            with httpx.Client(verify=ssl_cert, timeout=5.0) as http:
                resp = http.get(HEALTH_URL)
            if resp.status_code == 200:
                logger.info("Neo4j is healthy.")
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"Neo4j did not become healthy within {HEALTH_TIMEOUT_S}s")


def _apply_schema(driver) -> None:
    """Apply constraints and indexes."""
    with driver.session() as session:
        for cypher in CONSTRAINTS:
            logger.info("Applying: %s", cypher[:60])
            session.run(cypher)
    logger.info("Schema applied.")


def _verify_counts(driver) -> dict[str, int]:
    """Return node and relationship counts by label/type."""
    counts = {}
    with driver.session() as session:
        for label, _ in NODE_CSVS:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt").single()
            counts[label] = result["cnt"]
        for rel_type, _ in EDGE_CSVS:
            result = session.run(
                f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS cnt"
            ).single()
            counts[rel_type] = result["cnt"]
    return counts


def run_import(data_dir: str = "data") -> dict[str, int]:
    """
    Full import workflow. Returns node/rel counts on success.

    Args:
        data_dir: Path to directory containing nodes/ and edges/ subdirectories.
    """
    data_path = Path(data_dir).resolve()
    if not data_path.is_dir():
        raise RuntimeError(f"Data directory not found: {data_path}")

    docker = _find_docker()
    logger.info("Using Docker at: %s", docker)

    _copy_csvs(docker, data_path)
    _stop_container(docker)
    _import_database(docker)
    _start_container(docker)
    _wait_for_health()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        _apply_schema(driver)
        counts = _verify_counts(driver)
    finally:
        driver.close()

    for name, count in counts.items():
        logger.info("  %s: %d", name, count)

    return counts
