"""
Request models for all API endpoints.
Preserves existing CodeRequest and CustomRule functionality with proper typing.
"""

from pydantic import BaseModel, Field, field_validator


class CodeRequest(BaseModel):
    """Request body for code analysis endpoints."""
    language: str = Field(..., description="Programming language: python, java, cpp")
    code: str = Field(..., description="Source code to analyze", max_length=100_000)
    enable_custom_rules: bool = Field(False, description="Whether to run custom rules")

    @field_validator("language")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        lang = v.lower().strip()
        aliases = {
            "py": "python",
            "python": "python",
            "java": "java",
            "cpp": "cpp",
            "c++": "cpp",
        }
        normalized = aliases.get(lang)
        if not normalized:
            raise ValueError(f"Unsupported language: {v}. Supported: python, java, cpp")
        return normalized


class CustomRuleCreate(BaseModel):
    """Request body for creating a custom rule."""
    name: str = Field(..., min_length=1, max_length=100, description="Rule name")
    language: str = Field("any", description="Target language or 'any'")
    type: str = Field("contains", description="Match type: 'contains' or 'regex'")
    pattern: str = Field(..., min_length=1, description="Search pattern")
    severity: str = Field("warning", description="Severity: error, warning, info")
    message: str = Field(..., min_length=1, description="Message when rule matches")
    enabled: bool = Field(True, description="Whether the rule is active")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        allowed = {"any", "python", "java", "cpp"}
        if v.lower().strip() not in allowed:
            raise ValueError(f"Invalid language. Allowed: {', '.join(sorted(allowed))}")
        return v.lower().strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"contains", "regex"}
        if v.lower().strip() not in allowed:
            raise ValueError(f"Invalid type. Allowed: {', '.join(sorted(allowed))}")
        return v.lower().strip()

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"error", "warning", "info"}
        if v.lower().strip() not in allowed:
            raise ValueError(f"Invalid severity. Allowed: {', '.join(sorted(allowed))}")
        return v.lower().strip()


class CustomRuleUpdate(BaseModel):
    """Request body for updating a custom rule (partial)."""
    name: str | None = None
    language: str | None = None
    type: str | None = None
    pattern: str | None = None
    severity: str | None = None
    message: str | None = None
    enabled: bool | None = None


class AIReviewRequest(BaseModel):
    """Request body for AI-powered code review."""
    code: str = Field(..., description="Source code to review", max_length=100_000)
    language: str = Field("python", description="Programming language")
    prompt_type: str = Field(
        "review",
        description="Type of AI analysis: review, explain, refactor, docstring, ask"
    )
    question: str | None = Field(
        None, description="Specific question (for 'ask' prompt_type)"
    )

    @field_validator("prompt_type")
    @classmethod
    def validate_prompt_type(cls, v: str) -> str:
        allowed = {"review", "explain", "refactor", "docstring", "ask"}
        if v.lower().strip() not in allowed:
            raise ValueError(f"Invalid prompt_type. Allowed: {', '.join(sorted(allowed))}")
        return v.lower().strip()
