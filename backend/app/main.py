"""
FastAPI Application Factory.

Replaces the monolithic app.py with a clean modular setup.
All functionality is preserved but organized into routers and services.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routers import health, analyze, rules, ai_review, analytics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Enterprise-grade source code analysis API. "
            "Provides syntax, quality, security, performance, and type analysis "
            "with AI-powered code review via Groq."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware — preserved from original
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router)
    app.include_router(analyze.router)
    app.include_router(rules.router)
    app.include_router(ai_review.router)
    app.include_router(analytics.router)

    logger.info(f"{settings.app_name} v{settings.app_version} initialized")

    return app


# Application instance
app = create_app()
