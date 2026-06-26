"""
Health check and root API routes.
"""

from fastapi import APIRouter
from ..models.responses import HealthResponse
from ..config import get_settings
from ..utils.tool_runner import check_tool_available

router = APIRouter(tags=["Health"])


@router.get("/", summary="API root")
async def root():
    """Root endpoint showing API status."""
    settings = get_settings()
    return {
        "message": f"{settings.app_name} API is running",
        "version": settings.app_version,
    }


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health():
    """Health check endpoint with tool availability info."""
    settings = get_settings()

    tools = []
    for tool in ["pylint", "flake8", "bandit", "mypy", "pip_audit"]:
        if check_tool_available(tool):
            tools.append(tool)

    return HealthResponse(
        status="running",
        version=settings.app_version,
        tools_available=tools,
    )
