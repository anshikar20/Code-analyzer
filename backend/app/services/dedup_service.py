"""
Deduplication and ranking service.

Merges duplicate findings from different tools (e.g., pylint E0602 and flake8 F821
both report "undefined name") and ranks results by severity importance.
"""

import logging
from ..models.responses import Finding, Severity

logger = logging.getLogger(__name__)

# Known cross-tool duplicates: maps (tool, rule_id) -> canonical group
KNOWN_DUPLICATES: dict[tuple[str, str], str] = {
    # Undefined name
    ("pylint", "E0602"): "undefined-name",
    ("flake8", "F821"): "undefined-name",
    # Unused import
    ("pylint", "W0611"): "unused-import",
    ("flake8", "F401"): "unused-import",
    # Unused variable
    ("pylint", "W0612"): "unused-variable",
    ("flake8", "F841"): "unused-variable",
    # Redefined unused
    ("pylint", "W0404"): "reimported",
    ("flake8", "F811"): "reimported",
    # Line too long
    ("pylint", "C0301"): "line-too-long",
    ("flake8", "E501"): "line-too-long",
    # Missing whitespace
    ("pylint", "C0303"): "trailing-whitespace",
    ("flake8", "W291"): "trailing-whitespace",
    # Blank lines
    ("pylint", "C0303"): "blank-lines",
    ("flake8", "E302"): "blank-lines",
    ("flake8", "E303"): "blank-lines",
}

# Severity rank for sorting (lower = more important = shows first)
SEVERITY_RANK = {
    Severity.CRITICAL: 0,
    Severity.ERROR: 1,
    Severity.WARNING: 2,
    Severity.INFO: 3,
}

# Preferred tool when duplicates exist (higher quality messaging)
TOOL_PRIORITY = {
    "bandit": 0,     # Security findings are most specific
    "mypy": 1,       # Type errors are precise
    "pylint": 2,     # Better messages than flake8
    "flake8": 3,     # Often duplicates pylint
    "ast": 4,        # Basic syntax
    "custom": 5,     # User-defined
}


def deduplicate_findings(findings: list[Finding]) -> tuple[list[Finding], int]:
    """
    Remove duplicate findings that report the same issue from different tools.

    Returns:
        (deduplicated_findings, count_of_removed_duplicates)
    """
    if not findings:
        return [], 0

    # Group by (line, canonical_group) for known duplicates
    groups: dict[str, list[Finding]] = {}
    ungrouped: list[Finding] = []

    for finding in findings:
        group_key = KNOWN_DUPLICATES.get((finding.source, finding.rule_id))

        if group_key and finding.line:
            key = f"{finding.line}:{group_key}"
            groups.setdefault(key, []).append(finding)
        else:
            ungrouped.append(finding)

    # For each group, keep the finding from the highest-priority tool
    deduplicated: list[Finding] = []
    removed_count = 0

    for key, group in groups.items():
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            # Sort by tool priority, keep the best one
            group.sort(key=lambda f: TOOL_PRIORITY.get(f.source, 99))
            deduplicated.append(group[0])
            removed_count += len(group) - 1

    # Also deduplicate ungrouped by exact (line, message_hash)
    seen_fingerprints: set[str] = set()
    for finding in ungrouped:
        fp = f"{finding.line}:{finding.message[:50]}"
        if fp not in seen_fingerprints:
            seen_fingerprints.add(fp)
            deduplicated.append(finding)
        else:
            removed_count += 1

    logger.debug(f"Dedup: {len(findings)} → {len(deduplicated)} (removed {removed_count})")
    return deduplicated, removed_count


def rank_findings(findings: list[Finding]) -> list[Finding]:
    """
    Sort findings by importance: severity first, then category, then line number.
    Critical/error issues appear before warnings and info.
    """
    return sorted(findings, key=lambda f: (
        SEVERITY_RANK.get(f.severity, 99),
        f.category.value,
        f.line or 0,
    ))
