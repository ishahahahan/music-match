"""MusicMatch FastAPI application — see IMPLEMENTATION_ROADMAP.md."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import responses
from app.api.v1 import api_router
from app.config import settings

ENVELOPE_NOTE = (
    "Every /api/v1 response is wrapped in a uniform envelope: "
    "success bodies are {data, request_id, timestamp}; errors are "
    "{error: {code, message, details?}, request_id, timestamp}. "
    "Authenticate with Authorization: Bearer <JWT> — tokens never appear in URLs."
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="MusicMatch API",
        version="0.1.0",
        description=(
            "Mobile-ready REST API: login, auto-profiles, compatibility matching. " + ENVELOPE_NOTE
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(api_router, prefix="/api/v1")
    responses.install(app)  # Phase 5 envelope, error model, request-ID logs
    return app


app = create_app()
