"""
Structured response models for all API endpoints.

This is the CRITICAL change that transforms raw tool output dumps
into clean, deduplicated, ranked, human-friendly findings.

Before: Raw pylint/flake8 output as a single text blob
After:  Individual findings with title, explanation, fix suggestion, severity ranking
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# ─── Enums ─────────────────────────────────────────────

class Severity(str, Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Category(str, Enum):
    SYNTAX = "syntax"
    QUALITY = "quality"
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TYPE = "type"
    DEPENDENCY = "dependency"
    STRUCTURE = "structure"
    CUSTOM = "custom"


class Confidence(str, Enum):
    CONFIRMED = "confirmed"       # Parser/compiler confirmed
    HEURISTIC = "heuristic"       # Pattern-based, may be false positive
    AI_SUGGESTED = "ai-suggested" # Suggested by Gemini


# ─── Finding (individual issue) ────────────────────────

class Finding(BaseModel):
    """A single structured issue found during analysis."""
    id: str = Field(..., description="Unique fingerprint for dedup (hash of key fields)")
    category: Category = Field(..., description="Issue category")
    severity: Severity = Field(..., description="Severity level")
    confidence: Confidence = Field(Confidence.CONFIRMED, description="How certain is this finding")
    title: str = Field(..., description="Short human-readable title")
    message: str = Field(..., description="Detailed explanation")
    suggestion: str | None = Field(None, description="Fix recommendation")
    line: int | None = Field(None, description="1-indexed line number")
    column: int | None = Field(None, description="1-indexed column number")
    end_line: int | None = Field(None, description="End line for range highlighting")
    end_column: int | None = Field(None, description="End column for range highlighting")
    rule_id: str = Field("", description="Rule code (e.g., C0114, E302, B105)")
    source: str = Field("analyzer", description="Tool that produced this finding")


# ─── Score Breakdown ───────────────────────────────────

class ScoreBreakdown(BaseModel):
    """Composite quality scores (0-100, higher is better)."""
    overall: int = Field(100, ge=0, le=100)
    quality: int = Field(100, ge=0, le=100)
    security: int = Field(100, ge=0, le=100)
    performance: int = Field(100, ge=0, le=100)
    maintainability: int = Field(100, ge=0, le=100)


# ─── Issue Summary ─────────────────────────────────────

class SeverityCounts(BaseModel):
    critical: int = 0
    error: int = 0
    warning: int = 0
    info: int = 0


class CategoryCounts(BaseModel):
    syntax: int = 0
    quality: int = 0
    style: int = 0
    security: int = 0
    performance: int = 0
    type: int = 0
    dependency: int = 0
    structure: int = 0
    custom: int = 0


class IssueSummary(BaseModel):
    """Aggregated counts by severity and category."""
    total: int = 0
    by_severity: SeverityCounts = Field(default_factory=SeverityCounts)
    by_category: CategoryCounts = Field(default_factory=CategoryCounts)


# ─── Analysis Metadata ─────────────────────────────────

class AnalysisMetadata(BaseModel):
    """Metadata about the analysis run itself."""
    analysis_time_ms: int = Field(0, description="Total analysis time in milliseconds")
    tools_used: list[str] = Field(default_factory=list)
    dedup_removed: int = Field(0, description="Number of duplicate findings merged")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ─── Main Analysis Response ────────────────────────────

class AnalysisResponse(BaseModel):
    """
    The complete structured analysis response.

    This replaces the old flat dict with raw tool output blobs.
    Every field is typed, documented, and ready for frontend rendering.
    """
    status: str = Field("completed", description="completed | error")
    language: str = Field(..., description="Analyzed language")
    mode: str = Field("full", description="quick | full")
    scores: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    summary: IssueSummary = Field(default_factory=IssueSummary)
    findings: list[Finding] = Field(default_factory=list, description="Deduplicated, ranked findings")
    metadata: AnalysisMetadata = Field(default_factory=AnalysisMetadata)


# ─── Error Response ────────────────────────────────────

class ErrorResponse(BaseModel):
    """Structured error response with proper HTTP semantics."""
    status: str = "error"
    error_code: str
    message: str
    details: str | None = None


# ─── Custom Rule Responses ─────────────────────────────

class CustomRuleResponse(BaseModel):
    """Response after a custom rule operation."""
    status: str = "completed"
    message: str
    rule: dict | None = None


class CustomRulesListResponse(BaseModel):
    """Response listing all custom rules."""
    status: str = "completed"
    total: int = 0
    rules: list[dict] = Field(default_factory=list)


# ─── AI Review Response ────────────────────────────────

class AIReviewResponse(BaseModel):
    """Response from AI review endpoints."""
    status: str = "completed"
    prompt_type: str
    content: str = Field(..., description="Markdown-formatted AI response")
    model_used: str = Field("", description="Which Gemini model was used")
    tokens_used: int | None = Field(None, description="Approximate tokens consumed")


# ─── Dependency Response ───────────────────────────────

class DependencyFinding(BaseModel):
    """A single dependency issue."""
    package: str
    current_version: str = ""
    severity: Severity = Severity.WARNING
    vulnerability: str = ""
    fix_version: str = ""
    advisory_url: str = ""


class DependencyResponse(BaseModel):
    """Structured dependency scan response."""
    status: str = "completed"
    total: int = 0
    findings: list[DependencyFinding] = Field(default_factory=list)
    summary: SeverityCounts = Field(default_factory=SeverityCounts)


# ─── Health Response ───────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "running"
    version: str = ""
    tools_available: list[str] = Field(default_factory=list)
