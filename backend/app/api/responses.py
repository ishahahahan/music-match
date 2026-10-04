"""API contract hardening (roadmap Phase 5).

Every /api/v1 response is wrapped in one envelope so a mobile client can parse
a single shape:

    success -> {"data": ..., "request_id": "...", "timestamp": "..."}
    error   -> {"error": {"code": 404, "message": "...", "details": ...},
                "request_id": "...", "timestamp": "..."}

request_id is minted per request, attached to logs, and echoed in the body.
Timestamps are computed per response (the legacy backend evaluated one
``datetime.now()`` at import time — see roadmap Phase 5).
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger("musicmatch.http")

# Framework/metadata routes are not part of the product envelope.
_UNWRAPPED_PREFIXES = ("/docs", "/redoc", "/openapi.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "") or uuid.uuid4().hex


def error_envelope(
    request: Request, status_code: int, message: str, details: object | None = None
) -> dict:
    error: dict = {"code": status_code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error, "request_id": _request_id(request), "timestamp": _now()}


def install(app: FastAPI) -> None:
    """Attach the envelope middleware and error handlers to an app instance."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    @app.middleware("http")
    async def envelope_middleware(request: Request, call_next):  # noqa: ANN001
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Never log headers/bodies/query strings — tokens must not leak.
            logger.exception(
                "unhandled_error request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            raise
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "request request_id=%s method=%s path=%s status=%d duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        if response.status_code >= 400 or request.url.path.startswith(_UNWRAPPED_PREFIXES):
            return response

        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            payload = json.loads(body)
        except ValueError:
            return response  # non-JSON body (e.g. /docs HTML) — leave as-is
        wrapped = JSONResponse(
            content={"data": payload, "request_id": request_id, "timestamp": _now()},
            status_code=response.status_code,
        )
        for header, value in response.headers.items():
            if header.lower() not in {"content-length", "content-type"}:
                wrapped.headers[header] = value
        return wrapped

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, str):
            message, details = exc.detail, None
        else:
            message, details = "Request failed", exc.detail
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(request, exc.status_code, message, details),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_envelope(request, 422, "Request validation failed", details),
        )
