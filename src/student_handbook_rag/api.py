"""Single-process HTTP service for trusted use on this computer only."""

import argparse
import hmac
import json
import logging
import os
import threading
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from student_handbook_rag.chain import StudentHandbookRAG
from student_handbook_rag.config import (
    MAX_QUESTION_LENGTH,
    RETRIEVAL_K,
    frontend_origins,
    validate_config,
)
from student_handbook_rag.doctor import check_models
from student_handbook_rag.vectorstore import read_manifest, validate_source

logger = logging.getLogger("utc.api")


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    k: int = Field(default=RETRIEVAL_K, ge=1, le=10, strict=True)


class Citation(BaseModel):
    document: str
    document_id: str = Field(
        description="Portable document filename; not a local path or version hash."
    )
    source: str = Field(description="Compatibility alias of document_id; never a filesystem path.")
    page: int | None = Field(description="One-based PDF page.")
    book_page: int | None = Field(
        description="Estimated printed page: PDF page minus two, or zero for front matter."
    )
    section: str | None = Field(
        description="Page-level heading estimate; verify against the excerpt."
    )
    chunk_id: str
    score: float = Field(description="Legacy context order, not similarity or confidence.")
    context_rank: int = Field(
        ge=1, description="One-based position in the final generation context."
    )
    retrieval_rank: int | None = Field(
        ge=1, description="Original retrieval position; null for added page continuations."
    )
    excerpt: str


class Answer(BaseModel):
    query: str
    answer: str
    sources: list[Citation]
    is_insufficient_context: bool
    status: Literal["answered", "refused"]


class ServiceError(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: str | ServiceError


class Health(BaseModel):
    status: Literal["ok"]
    version: str


class Readiness(BaseModel):
    status: Literal["ready"]


bearer = HTTPBearer(auto_error=False, description="Required only when RAG_API_KEY is configured.")


class BodyLimitMiddleware:
    """Bound the body before FastAPI JSON parsing, including chunked requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 16384:
                return await JSONResponse({"detail": "Request body too large"}, 413)(
                    scope, receive, send
                )
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


def check_active_index(engine):
    manifest = read_manifest()
    validate_source(manifest)
    collection = engine.retriever.vector_db._collection
    if collection.name != manifest["collection"] or collection.count() != manifest["chunk_count"]:
        raise RuntimeError("Restart required after ingestion")


def create_app(
    engine_factory=StudentHandbookRAG, readiness_check=check_models, index_check=check_active_index
):
    gate = threading.BoundedSemaphore(1)
    rate_lock = threading.Lock()
    recent = deque()
    api_key = os.getenv("RAG_API_KEY", "")
    allowed_origins = frontend_origins()

    @asynccontextmanager
    async def lifespan(app):
        validate_config()
        app.state.engine = await run_in_threadpool(engine_factory)
        yield

    app = FastAPI(
        title="UTC Student Handbook RAG", version=version("student-handbook-rag"), lifespan=lifespan
    )
    app.add_middleware(BodyLimitMiddleware)

    @app.middleware("http")
    async def authenticate_and_handle_errors(request, call_next):
        if (
            request.url.path == "/ask"
            and api_key
            and not hmac.compare_digest(
                request.headers.get("authorization", "").encode(), f"Bearer {api_key}".encode()
            )
        ):
            return JSONResponse(
                {"detail": "Unauthorized"}, 401, headers={"WWW-Authenticate": "Bearer"}
            )
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(
                "request_failed error_type=%s request_id=%s",
                type(exc).__name__,
                request.state.request_id,
            )
            return JSONResponse({"detail": "Service temporarily unavailable"}, 503)

    # CORS wraps authentication and service errors so a trusted browser can read them.
    # Preflight is handled here before bearer authentication or inference.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(allowed_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID", "Retry-After"],
        allow_credentials=False,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])

    @app.middleware("http")
    async def request_metadata(request, call_next):
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.monotonic()
        # Reject untrusted browser writes before they can trigger local inference.
        origin = request.headers.get("origin")
        if (
            origin is not None
            and origin != str(request.base_url).rstrip("/")
            and origin not in allowed_origins
        ):
            response = JSONResponse({"detail": "Origin not allowed"}, 403)
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - start) * 1000),
                }
            )
        )
        return response

    @app.get("/health", response_model=Health)
    def health():
        return {"status": "ok", "version": app.version}

    @app.get("/ready", response_model=Readiness, responses={503: {"model": ErrorResponse}})
    def ready():
        try:
            readiness_check()
            index_check(app.state.engine)
        except Exception:
            raise HTTPException(503, "Dependencies not ready; run utc-doctor") from None
        return {"status": "ready"}

    @app.post(
        "/ask",
        response_model=Answer,
        responses={code: {"model": ErrorResponse} for code in (401, 403, 413, 429, 503)},
    )
    def ask(
        payload: Question,
        request: Request,
        _credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
    ):
        now = time.monotonic()
        with rate_lock:
            while recent and recent[0] <= now - 60:
                recent.popleft()
            if len(recent) >= 30:
                raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": "60"})
            recent.append(now)
        if not gate.acquire(blocking=False):
            raise HTTPException(429, "Inference busy; retry shortly", headers={"Retry-After": "5"})
        try:
            try:
                index_check(request.app.state.engine)
            except Exception:
                raise HTTPException(503, "Index not ready; run utc-doctor and restart") from None
            result = request.app.state.engine.query(payload.question, k=payload.k)
            if result.get("status") == "error":
                raise HTTPException(
                    503, {"code": result["error_code"], "message": result["answer"]}
                )
            return {key: value for key, value in result.items() if key != "retrieved_chunks"}
        finally:
            gate.release()

    return app


app = create_app()


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Serve UTC RAG on this computer")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    uvicorn.run(
        "student_handbook_rag.api:app",
        host="127.0.0.1",
        port=args.port,
        workers=1,
        proxy_headers=False,
        access_log=False,
        limit_concurrency=16,
        timeout_keep_alive=5,
    )


if __name__ == "__main__":
    main()
