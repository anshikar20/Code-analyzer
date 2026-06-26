"""
Code quality scoring service.

Computes quality, security, performance, and maintainability scores
from analysis findings. Provides meaningful metrics for the dashboard.
"""

from ..models.responses import (
    Finding, Severity, Category,
    ScoreBreakdown, IssueSummary, SeverityCounts, CategoryCounts
)


# Penalty weights per severity level
SEVERITY_PENALTY = {
    Severity.CRITICAL: 25,
    Severity.ERROR: 15,
    Severity.WARNING: 5,
    Severity.INFO: 1,
}

# Which categories affect which scores
CATEGORY_SCORE_MAP: dict[Category, list[str]] = {
    Category.SYNTAX: ["quality", "overall"],
    Category.QUALITY: ["quality", "maintainability", "overall"],
    Category.STYLE: ["maintainability", "overall"],
    Category.SECURITY: ["security", "overall"],
    Category.PERFORMANCE: ["performance", "overall"],
    Category.TYPE: ["quality", "overall"],
    Category.DEPENDENCY: ["security", "overall"],
    Category.STRUCTURE: ["maintainability", "overall"],
    Category.CUSTOM: ["quality", "overall"],
}


def compute_scores(findings: list[Finding]) -> ScoreBreakdown:
    """
    Compute quality scores from findings.

    Each finding penalizes relevant scores based on severity.
    Scores start at 100 and decrease. Minimum is 0.
    """
    penalties = {
        "overall": 0,
        "quality": 0,
        "security": 0,
        "performance": 0,
        "maintainability": 0,
    }

    for finding in findings:
        penalty = SEVERITY_PENALTY.get(finding.severity, 1)
        affected_scores = CATEGORY_SCORE_MAP.get(finding.category, ["overall"])

        for score_name in affected_scores:
            penalties[score_name] += penalty

    return ScoreBreakdown(
        overall=max(0, 100 - penalties["overall"]),
        quality=max(0, 100 - penalties["quality"]),
        security=max(0, 100 - penalties["security"]),
        performance=max(0, 100 - penalties["performance"]),
        maintainability=max(0, 100 - penalties["maintainability"]),
    )


def compute_summary(findings: list[Finding]) -> IssueSummary:
    """
    Aggregate finding counts by severity and category.
    """
    by_severity = SeverityCounts()
    by_category = CategoryCounts()

    for finding in findings:
        # Count by severity
        match finding.severity:
            case Severity.CRITICAL:
                by_severity.critical += 1
            case Severity.ERROR:
                by_severity.error += 1
            case Severity.WARNING:
                by_severity.warning += 1
            case Severity.INFO:
                by_severity.info += 1

        # Count by category
        cat_name = finding.category.value
        if hasattr(by_category, cat_name):
            current = getattr(by_category, cat_name)
            setattr(by_category, cat_name, current + 1)

    return IssueSummary(
        total=len(findings),
        by_severity=by_severity,
        by_category=by_category,
    )
