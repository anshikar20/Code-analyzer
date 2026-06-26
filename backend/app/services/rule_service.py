"""
Custom rule management service.

Preserves all custom rule functionality from original app.py
(load, save, match, CRUD) but with proper structure.
"""

import re
import json
import hashlib
import logging
from pathlib import Path
from ..models.responses import Finding, Severity, Category, Confidence
from ..config import get_settings

logger = logging.getLogger(__name__)


def _get_rules_path() -> Path:
    """Get the path to the custom rules JSON file."""
    settings = get_settings()
    return Path(settings.custom_rules_file)


def load_custom_rules() -> list[dict]:
    """Load custom rules from the JSON file."""
    rules_path = _get_rules_path()

    if not rules_path.exists():
        return []

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = json.load(f)
        return rules if isinstance(rules, list) else []
    except Exception as e:
        logger.error(f"Failed to load custom rules: {e}")
        return []


def save_custom_rules(rules: list[dict]) -> None:
    """Save custom rules to the JSON file."""
    rules_path = _get_rules_path()
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)


def add_custom_rule(rule: dict) -> list[dict]:
    """Add a new custom rule and return the updated list."""
    rules = load_custom_rules()
    rules.append(rule)
    save_custom_rules(rules)
    return rules


def update_custom_rule(index: int, updates: dict) -> tuple[list[dict], dict | None]:
    """Update a custom rule at the given index."""
    rules = load_custom_rules()
    if index < 0 or index >= len(rules):
        return rules, None
    for key, value in updates.items():
        if value is not None:
            rules[index][key] = value
    save_custom_rules(rules)
    return rules, rules[index]


def toggle_custom_rule(index: int) -> tuple[list[dict], dict | None]:
    """Toggle the enabled status of a rule."""
    rules = load_custom_rules()
    if index < 0 or index >= len(rules):
        return rules, None
    rules[index]["enabled"] = not rules[index].get("enabled", True)
    save_custom_rules(rules)
    return rules, rules[index]


def delete_custom_rule(index: int) -> tuple[list[dict], dict | None]:
    """Delete a custom rule at the given index."""
    rules = load_custom_rules()
    if index < 0 or index >= len(rules):
        return rules, None
    deleted = rules.pop(index)
    save_custom_rules(rules)
    return rules, deleted


def _make_id(line: int | None, rule_name: str, message: str) -> str:
    raw = f"custom:{line or 0}:{rule_name}:{message[:80]}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _map_severity(severity_str: str) -> Severity:
    mapping = {
        "error": Severity.ERROR,
        "warning": Severity.WARNING,
        "info": Severity.INFO,
    }
    return mapping.get(severity_str.lower(), Severity.WARNING)


def run_custom_rules(code: str, language: str) -> list[Finding]:
    """
    Execute custom rules against the provided code.
    Preserved from original app.py lines 438-490.
    """
    findings: list[Finding] = []
    rules = load_custom_rules()

    for rule in rules:
        if not rule.get("enabled", True):
            continue

        rule_language = rule.get("language", "any").lower().strip()
        if rule_language != "any" and rule_language != language:
            continue

        rule_name = rule.get("name", "Unnamed custom rule")
        rule_type = rule.get("type", "contains")
        pattern = rule.get("pattern", "")
        severity = rule.get("severity", "warning")
        message = rule.get("message", "Custom rule matched.")

        if not pattern:
            continue

        for line_number, line in enumerate(code.splitlines(), start=1):
            matched = False

            if rule_type == "contains":
                matched = pattern in line
            elif rule_type == "regex":
                try:
                    matched = re.search(pattern, line) is not None
                except re.error:
                    findings.append(Finding(
                        id=_make_id(None, rule_name, "Invalid regex"),
                        category=Category.CUSTOM,
                        severity=Severity.WARNING,
                        confidence=Confidence.CONFIRMED,
                        title=f"Invalid regex in rule '{rule_name}'",
                        message=f"The regex pattern in rule '{rule_name}' is invalid.",
                        suggestion="Check the regex syntax in the custom rule configuration.",
                        rule_id="REGEX_ERROR",
                        source="custom-rule-engine",
                    ))
                    break

            if matched:
                findings.append(Finding(
                    id=_make_id(line_number, rule_name, message),
                    category=Category.CUSTOM,
                    severity=_map_severity(severity),
                    confidence=Confidence.HEURISTIC,
                    title=rule_name,
                    message=message,
                    line=line_number,
                    rule_id=f"CUSTOM:{rule_name}",
                    source=f"custom-rule-engine",
                ))

    return findings
