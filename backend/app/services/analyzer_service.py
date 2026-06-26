"""
Main analysis orchestration service.

Coordinates the full analysis pipeline:
1. Route to correct language analyzer
2. Run custom rules (if enabled)
3. Deduplicate findings
4. Rank by severity
5. Compute scores
6. Build structured response
"""

import time
import logging
from ..models.responses import (
    AnalysisResponse, AnalysisMetadata, Finding
)
from ..analyzers.python_analyzer import PythonAnalyzer
from ..analyzers.multilang_analyzer import JavaAnalyzer, CppAnalyzer
from ..services.dedup_service import deduplicate_findings, rank_findings
from ..services.scoring_service import compute_scores, compute_summary
from ..services.rule_service import run_custom_rules
from ..config import get_settings

logger = logging.getLogger(__name__)

# Singleton analyzers
_python_analyzer = PythonAnalyzer()
_java_analyzer = JavaAnalyzer()
_cpp_analyzer = CppAnalyzer()


def get_analyzer(language: str):
    """Route to the correct language analyzer."""
    analyzers = {
        "python": _python_analyzer,
        "java": _java_analyzer,
        "cpp": _cpp_analyzer,
    }
    return analyzers.get(language)


def analyze_code(
    code: str,
    language: str,
    mode: str = "full",
    enable_custom_rules: bool = False,
) -> AnalysisResponse:
    """
    Run the complete analysis pipeline and return a structured response.

    This is the main entry point that replaces the old analyze_full/analyze_quick
    functions from app.py, with proper output processing.
    """
    settings = get_settings()
    start_time = time.time()

    analyzer = get_analyzer(language)
    if not analyzer:
        return AnalysisResponse(
            status="error",
            language=language,
            mode=mode,
            metadata=AnalysisMetadata(
                analysis_time_ms=0,
                tools_used=[],
            ),
        )

    # 1. Run language-specific analysis
    if mode == "quick":
        raw_findings = analyzer.quick_analyze(code)
    else:
        raw_findings = analyzer.full_analyze(code)

    # 2. Run custom rules (if enabled)
    if enable_custom_rules:
        custom_findings = run_custom_rules(code, language)
        raw_findings.extend(custom_findings)

    # 3. Deduplicate
    findings, dedup_removed = deduplicate_findings(raw_findings)

    # 4. Rank by severity
    findings = rank_findings(findings)

    # 5. Compute scores
    scores = compute_scores(findings)

    # 6. Compute summary
    summary = compute_summary(findings)

    # 7. Build metadata
    elapsed_ms = int((time.time() - start_time) * 1000)
    metadata = AnalysisMetadata(
        analysis_time_ms=elapsed_ms,
        tools_used=analyzer.get_tools_used(),
        dedup_removed=dedup_removed,
    )

    return AnalysisResponse(
        status="completed",
        language=language,
        mode=mode,
        scores=scores,
        summary=summary,
        findings=findings,
        metadata=metadata,
    )
