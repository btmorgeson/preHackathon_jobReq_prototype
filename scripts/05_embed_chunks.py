"""
Phase 5: Embed Chunk and Role nodes, then create vector indexes.

Usage:
    python scripts/05_embed_chunks.py

Requires:
    - GENESIS_SKLZ_API_KEY set in environment
    - Neo4j container running and data already imported (run 04_neo4j_import.py first)
"""
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password12345")

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


def create_vector_indexes(driver) -> None:
    """Create vector indexes for chunk and role embeddings."""
    with driver.session() as session:
        for cypher, index_name in VECTOR_INDEXES:
            try:
                session.run(cypher)
                logger.info("Created vector index: %s", index_name)
            except Exception as exc:
                if "already exists" in str(exc).lower():
                    logger.info("Vector index already exists (skipping): %s", index_name)
                else:
                    raise


def main() -> None:
    from neo4j import GraphDatabase
    from src.pipeline.embed.embed_pipeline import run_embed_pipeline

    logger.info("Starting embedding pipeline...")
    try:
        run_embed_pipeline()
    except KeyError as exc:
        logger.error("Missing required environment variable: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Embed pipeline failed: %s", exc)
        sys.exit(1)

    logger.info("Creating vector indexes...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        create_vector_indexes(driver)
    except Exception as exc:
        logger.error("Failed to create vector indexes: %s", exc)
        sys.exit(1)
    finally:
        driver.close()

    print("\nEmbedding pipeline complete.")
    print("Vector indexes created:")
    for _, index_name in VECTOR_INDEXES:
        print(f"  - {index_name}")


if __name__ == "__main__":
    main()
