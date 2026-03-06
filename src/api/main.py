"""FastAPI application â€” LMCO HR AI Hackathon talent-matching API."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError


def _sanitize_validation_errors(errors: list) -> list:
    """Strip non-JSON-serializable values (e.g., Exception objects in ctx) from Pydantic v2 errors."""
    result = []
    for err in errors:
        sanitized = {k: v for k, v in err.items() if k not in ("ctx", "url")}
        if "ctx" in err:
            sanitized["ctx"] = {
                k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                for k, v in err["ctx"].items()
            }
        result.append(sanitized)
    return result

from src.api.deps import close_driver, get_driver
from src.api.models import ErrorResponse
from src.api.routers import postings, search, skills
from src.config import get_settings

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid4()))


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error={
            "code": code,
            "message": message,
            "request_id": _request_id(request),
            "details": details,
        }
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@asynccontextmanager
async def lifespan(app: FastAPI):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("MATCH (n) RETURN count(n) LIMIT 1").data()
        logger.info("Neo4j connection verified")
    except Exception as exc:
        logger.error("Neo4j connection failed on startup: %s", exc)
        raise

    yield

    close_driver()
    logger.info("Neo4j driver closed")


app = FastAPI(
    title="LMCO HR Talent Matching API",
    description="Rank synthetic employees against job requirements using Neo4j + Genesis LLM.",
    version="0.2.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request.complete request_id=%s method=%s path=%s status=%d duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(
        request=request,
        status_code=422,
        code="validation_error",
        message="Request validation failed.",
        details=_sanitize_validation_errors(exc.errors()),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Request failed."
    return _error_response(
        request=request,
        status_code=exc.status_code,
        code="http_error",
        message=message,
        details=None if isinstance(detail, str) else detail,
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
    return _error_response(
        request=request,
        status_code=422,
        code="validation_error",
        message="Request validation failed.",
        details=_sanitize_validation_errors(exc.errors()),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception request_id=%s", _request_id(request), exc_info=exc)
    return _error_response(
        request=request,
        status_code=500,
        code="internal_error",
        message="Internal server error.",
    )


app.include_router(search.router, prefix="/api")
app.include_router(postings.router, prefix="/api")
app.include_router(skills.router, prefix="/api")


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
