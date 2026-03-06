"""
Embedding pipeline for Chunk and Role nodes.

Restart-safe: skips nodes that already have embeddings by default.
Can optionally rebuild embeddings and indexes.
"""

from __future__ import annotations

import logging
import re
from typing import Iterator

from neo4j import GraphDatabase

from src.config import get_settings
from src.pipeline.embed.genesis_client import BATCH_SIZE, embed_batch, make_client

logger = logging.getLogger(__name__)

VECTOR_INDEXES = [
    (
        "CALL db.index.vector.createNodeIndex('chunk_embedding_idx','Chunk','embedding',1024,'cosine')",
        "chunk_embedding_idx",
    ),
    (
        "CALL db.index.vector.createNodeIndex('role_title_idx','Role','title_embedding',1024,'cosine')",
        "role_title_idx",
    ),
]


def _batches(items: list, size: int) -> Iterator[list]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _link_chunk_to_skills(text: str, skill_names: list[str]) -> list[str]:
    """Return skill names that appear as whole words in text (case-insensitive).

    Uses word-boundary regex to avoid partial matches:
    e.g. skill "C" must not match inside "Cloud" or "CAD".
    """
    text_lower = text.lower()
    matched: list[str] = []
    for skill_name in skill_names:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill_name.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            matched.append(skill_name)
    return matched


def _clear_mentions_edges(driver) -> None:
    with driver.session() as session:
        session.run("MATCH ()-[r:MENTIONS]->() DELETE r")
    logger.info("Cleared all MENTIONS edges.")


def link_chunk_mentions(driver) -> int:
    """Link Chunk nodes to Skill nodes they mention via MENTIONS edges.

    Restart-safe: only processes chunks with no outgoing MENTIONS edges.
    Returns the count of new MENTIONS edges created.
    """
    with driver.session() as session:
        skill_records = session.run(
            "MATCH (s:Skill) RETURN s.name AS name, s.stable_id AS stable_id"
        ).data()

    if not skill_records:
        logger.info("No skills found — skipping MENTIONS linking.")
        return 0

    skill_pairs = [(r["name"], r["stable_id"]) for r in skill_records]
    skill_names = [name for name, _ in skill_pairs]
    skill_id_by_name = {name: sid for name, sid in skill_pairs}

    with driver.session() as session:
        chunk_records = session.run(
            "MATCH (c:Chunk) WHERE NOT (c)-[:MENTIONS]->() "
            "RETURN c.stable_id AS chunk_id, c.text AS text"
        ).data()

    if not chunk_records:
        logger.info("All chunks already have MENTIONS edges (or no chunks found).")
        return 0

    logger.info("Linking MENTIONS edges for %d unlinked chunks...", len(chunk_records))
    total_edges = 0

    for chunk_rec in chunk_records:
        chunk_id = chunk_rec["chunk_id"]
        matched_names = _link_chunk_to_skills(chunk_rec["text"], skill_names)
        if not matched_names:
            continue
        matched_skill_ids = [skill_id_by_name[name] for name in matched_names]
        with driver.session() as session:
            result = session.run(
                "MATCH (c:Chunk {stable_id: $chunk_id}) "
                "MATCH (s:Skill) WHERE s.stable_id IN $skill_ids "
                "MERGE (c)-[:MENTIONS]->(s) "
                "RETURN count(*) AS edges_created",
                chunk_id=chunk_id,
                skill_ids=matched_skill_ids,
            )
            total_edges += result.single()["edges_created"]

    logger.info("Created %d MENTIONS edges.", total_edges)
    return total_edges


def _clear_existing_embeddings(driver) -> None:
    with driver.session() as session:
        session.run("MATCH (c:Chunk) REMOVE c.embedding")
        session.run("MATCH (r:Role) REMOVE r.title_embedding")
    logger.info("Removed existing chunk and role embeddings.")


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
        texts = [record["text"] for record in batch]
        embeddings = embed_batch(client, texts)
        with driver.session() as session:
            for record, embedding in zip(batch, embeddings):
                session.run(
                    "MATCH (c:Chunk {stable_id: $id}) SET c.embedding = $emb",
                    id=record["id"],
                    emb=embedding,
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
        texts = [record["title"] for record in batch]
        embeddings = embed_batch(client, texts)
        with driver.session() as session:
            for record, embedding in zip(batch, embeddings):
                session.run(
                    "MATCH (r:Role {stable_id: $id}) SET r.title_embedding = $emb",
                    id=record["id"],
                    emb=embedding,
                )
        count += len(batch)
        logger.info("  Embedded %d/%d roles", count, len(records))

    return count


def ensure_vector_indexes(driver, rebuild_indexes: bool = False) -> list[str]:
    """Create vector indexes for chunk and role embeddings."""
    created_or_existing: list[str] = []
    with driver.session() as session:
        if rebuild_indexes:
            for _, index_name in VECTOR_INDEXES:
                try:
                    session.run(f"DROP INDEX {index_name} IF EXISTS")
                except Exception:
                    logger.warning("Unable to drop index %s; continuing.", index_name)

        for cypher, index_name in VECTOR_INDEXES:
            try:
                session.run(cypher)
                logger.info("Created vector index: %s", index_name)
            except Exception as exc:
                if "already exists" in str(exc).lower():
                    logger.info("Vector index already exists (skipping): %s", index_name)
                else:
                    raise
            created_or_existing.append(index_name)
    return created_or_existing


def run_embed_pipeline(
    rebuild_embeddings: bool = False,
    rebuild_indexes: bool = False,
    rebuild_mentions: bool = False,
) -> dict[str, object]:
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    client = make_client()
    try:
        if rebuild_embeddings:
            _clear_existing_embeddings(driver)
        chunks_count = embed_chunks(driver, client)
        roles_count = embed_roles(driver, client)
        if rebuild_mentions:
            _clear_mentions_edges(driver)
        mentions_count = link_chunk_mentions(driver)
        indexes = ensure_vector_indexes(driver, rebuild_indexes=rebuild_indexes)
        logger.info(
            "Embed pipeline complete: chunks=%d, roles=%d, mentions=%d",
            chunks_count,
            roles_count,
            mentions_count,
        )
        return {
            "chunks_embedded": chunks_count,
            "roles_embedded": roles_count,
            "mentions_linked": mentions_count,
            "indexes": indexes,
        }
    finally:
        driver.close()
