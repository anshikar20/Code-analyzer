"""
Analysis API routes.

Replaces the monolithic /analyze, /analyze/quick, /analyze/full endpoints
from original app.py with clean route handlers that delegate to services.
"""

from fastapi import APIRouter, HTTPException
from ..models.requests import CodeRequest
from ..models.responses import AnalysisResponse, DependencyResponse, ErrorResponse
from ..services.analyzer_service import analyze_code
from ..services.parser_service import parse_pip_audit_output
from ..services.scoring_service import compute_summary, compute_scores
from ..services.history_service import history_service
from ..utils.tool_runner import run_python_tool

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post(
    "/quick",
    response_model=AnalysisResponse,
    summary="Quick analysis for real-time feedback",
    description="Fast lightweight analysis suitable for real-time typing feedback (AST + flake8)."
)
async def analyze_quick(request: CodeRequest):
    """Quick scan — runs AST + flake8 for fast feedback while typing."""
    response = analyze_code(
        code=request.code,
        language=request.language,
        mode="quick",
        enable_custom_rules=request.enable_custom_rules,
    )
    history_service.save_scan(response)
    return response


@router.post(
    "/full",
    response_model=AnalysisResponse,
    summary="Full comprehensive analysis",
    description="Runs all available tools (AST, pylint, flake8, bandit, mypy) for thorough analysis."
)
async def analyze_full(request: CodeRequest):
    """Full scan — comprehensive analysis with all tools."""
    response = analyze_code(
        code=request.code,
        language=request.language,
        mode="full",
        enable_custom_rules=request.enable_custom_rules,
    )
    history_service.save_scan(response)
    return response


@router.post(
    "",
    response_model=AnalysisResponse,
    summary="Default analysis (full)",
    description="Alias for /analyze/full."
)
async def analyze_default(request: CodeRequest):
    """Default endpoint — delegates to full analysis."""
    response = analyze_code(
        code=request.code,
        language=request.language,
        mode="full",
        enable_custom_rules=request.enable_custom_rules,
    )
    history_service.save_scan(response)
    return response


@router.get(
    "/dependencies",
    response_model=DependencyResponse,
    summary="Scan Python dependencies for vulnerabilities",
)
async def analyze_dependencies():
    """
    Run pip-audit to check for vulnerable packages.
    Preserved from original app.py lines 732-764 but with structured output.
    """
    stdout, stderr, rc = run_python_tool("pip_audit", [])
    combined = stdout + stderr

    if not combined.strip() or "No known vulnerabilities found" in combined:
        return DependencyResponse(status="completed", total=0, findings=[])

    findings = parse_pip_audit_output(combined)

    return DependencyResponse(
        status="completed",
        total=len(findings),
        findings=[
            {
                "package": f.title.replace("Vulnerable package: ", ""),
                "current_version": "",
                "severity": f.severity,
                "vulnerability": f.rule_id,
                "fix_version": "",
                "advisory_url": "",
            }
            for f in findings
        ],
        summary={"error": len([f for f in findings if f.severity.value in ("critical", "error")]),
                 "warning": len([f for f in findings if f.severity.value == "warning"]),
                 "info": len([f for f in findings if f.severity.value == "info"]),
                 "critical": 0},
    )
