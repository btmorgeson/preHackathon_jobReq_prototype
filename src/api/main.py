"""FastAPI application — LMCO HR AI Hackathon talent-matching API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import get_driver, close_driver
from src.api.routers import search, postings, skills

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify Neo4j reachability
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("MATCH (n) RETURN count(n) LIMIT 1").data()
        logger.info("Neo4j connection verified")
    except Exception as exc:
        logger.error("Neo4j connection failed on startup: %s", exc)
        raise

    yield

    # Shutdown: close driver
    close_driver()
    logger.info("Neo4j driver closed")


app = FastAPI(
    title="LMCO HR Talent Matching API",
    description="Rank synthetic employees against job requirements using Neo4j + Genesis LLM.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api")
app.include_router(postings.router, prefix="/api")
app.include_router(skills.router, prefix="/api")


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
