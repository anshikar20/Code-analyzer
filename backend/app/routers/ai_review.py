"""
AI review API routes.

Gemini-powered code analysis endpoints.
"""

from fastapi import APIRouter, HTTPException
from ..models.requests import AIReviewRequest
from ..models.responses import AIReviewResponse
from ..services.ai_service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Review"])


@router.post(
    "/review",
    response_model=AIReviewResponse,
    summary="AI-powered code review",
)
async def ai_review(request: AIReviewRequest):
    """Run Gemini AI code review."""
    content, model_used = await ai_service.process_request(
        code=request.code,
        language=request.language,
        prompt_type=request.prompt_type,
        question=request.question,
    )

    return AIReviewResponse(
        status="completed",
        prompt_type=request.prompt_type,
        content=content,
        model_used=model_used,
    )


@router.post(
    "/explain",
    response_model=AIReviewResponse,
    summary="AI code explanation",
)
async def ai_explain(request: AIReviewRequest):
    """Explain what the code does using Gemini."""
    content, model_used = await ai_service.explain_code(
        code=request.code, language=request.language
    )
    return AIReviewResponse(
        status="completed",
        prompt_type="explain",
        content=content,
        model_used=model_used,
    )


@router.post(
    "/refactor",
    response_model=AIReviewResponse,
    summary="AI refactoring suggestions",
)
async def ai_refactor(request: AIReviewRequest):
    """Get AI-powered refactoring suggestions."""
    content, model_used = await ai_service.refactor_code(
        code=request.code, language=request.language
    )
    return AIReviewResponse(
        status="completed",
        prompt_type="refactor",
        content=content,
        model_used=model_used,
    )


@router.post(
    "/docstring",
    response_model=AIReviewResponse,
    summary="Generate docstring",
)
async def ai_docstring(request: AIReviewRequest):
    """Generate a docstring for the given code."""
    content, model_used = await ai_service.generate_docstring(
        code=request.code, language=request.language
    )
    return AIReviewResponse(
        status="completed",
        prompt_type="docstring",
        content=content,
        model_used=model_used,
    )


@router.post(
    "/ask",
    response_model=AIReviewResponse,
    summary="Ask a question about code",
)
async def ai_ask(request: AIReviewRequest):
    """Ask a developer question about the code."""
    if not request.question:
        raise HTTPException(status_code=400, detail="'question' field is required for /ai/ask")

    content, model_used = await ai_service.ask_question(
        code=request.code,
        question=request.question,
        language=request.language,
    )
    return AIReviewResponse(
        status="completed",
        prompt_type="ask",
        content=content,
        model_used=model_used,
    )
