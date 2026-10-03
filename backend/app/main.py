"""MusicMatch FastAPI application — see IMPLEMENTATION_ROADMAP.md."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="MusicMatch API",
        version="0.1.0",
        description="Mobile-ready REST API: login, auto-profiles, compatibility matching.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
