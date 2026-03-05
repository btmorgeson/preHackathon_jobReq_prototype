"""
Embedding pipeline for Chunk and Role nodes.

Restart-safe: skips nodes that already have embeddings.
Reads all Chunk nodes without 'embedding' property, batches 25 at a time,
writes embedding back to Neo4j.
Then repeats for Role.title -> Role.title_embedding.
"""
import logging
import os
from typing import Iterator

from neo4j import GraphDatabase
from src.pipeline.embed.genesis_client import BATCH_SIZE, make_client, embed_batch

logger = logging.getLogger(__name__)

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password12345")


def _batches(items: list, size: int) -> Iterator[list]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def embed_chunks(driver, client) -> int:
    """Embed Chunk nodes missing embeddings. Returns count embedded."""
    with driver.session() as session:
        records = session.run(
            "MATCH (c:Chunk) WHERE c.embedding IS NULL RETURN c.stable_id AS id, c.text AS text"
        ).data()

    if not records:
        logger.info("No unembedded chunks found.")
        return 0

    logger.info("Embedding %d chunks...", len(records))
    count = 0
    for batch in _batches(records, BATCH_SIZE):
        texts = [r["text"] for r in batch]
        embeddings = embed_batch(client, texts)
        with driver.session() as session:
            for record, emb in zip(batch, embeddings):
                session.run(
                    "MATCH (c:Chunk {stable_id: $id}) SET c.embedding = $emb",
                    id=record["id"],
                    emb=emb,
                )
        count += len(batch)
        logger.info("  Embedded %d/%d chunks", count, len(records))

    return count


def embed_roles(driver, client) -> int:
    """Embed Role.title -> Role.title_embedding for roles missing it."""
    with driver.session() as session:
        records = session.run(
            "MATCH (r:Role) WHERE r.title_embedding IS NULL RETURN r.stable_id AS id, r.title AS title"
        ).data()

    if not records:
        logger.info("No unembedded roles found.")
        return 0

    logger.info("Embedding %d role titles...", len(records))
    count = 0
    for batch in _batches(records, BATCH_SIZE):
        texts = [r["title"] for r in batch]
        embeddings = embed_batch(client, texts)
        with driver.session() as session:
            for record, emb in zip(batch, embeddings):
                session.run(
                    "MATCH (r:Role {stable_id: $id}) SET r.title_embedding = $emb",
                    id=record["id"],
                    emb=emb,
                )
        count += len(batch)
        logger.info("  Embedded %d/%d roles", count, len(records))

    return count


def run_embed_pipeline() -> None:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    client = make_client()
    try:
        chunks_count = embed_chunks(driver, client)
        roles_count = embed_roles(driver, client)
        logger.info("Embed pipeline complete: chunks=%d, roles=%d", chunks_count, roles_count)
    finally:
        driver.close()
