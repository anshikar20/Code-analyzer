"""
Tool output parsers that transform raw text output from pylint, flake8, bandit, and mypy
into structured Finding objects.

This is THE critical missing piece in the old codebase.
Before: Raw tool output dumped as a single text blob.
After:  Individual parsed findings with line, column, rule_id, title, suggestion.
"""

import re
import hashlib
from ..models.responses import Finding, Severity, Category, Confidence

# ─── Fingerprinting ────────────────────────────────────

def _make_id(source: str, line: int | None, rule_id: str, message: str) -> str:
    """Generate a unique fingerprint for a finding for deduplication."""
    raw = f"{source}:{line or 0}:{rule_id}:{message[:80]}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]


# ─── Temp path stripping ───────────────────────────────

def _strip_temp_path(message: str) -> str:
    """Remove temporary file paths from messages so users never see them."""
    # Matches patterns like /tmp/analyzer_xyz123.py:1:0: or C:\\Users\\...\\tmp...py:
    message = re.sub(r"[\w/\\:.\-]+analyzer_\w+\.py:\d+:\d+:\s*", "", message)
    message = re.sub(r"[\w/\\:.\-]+tmp\w+\.py:\d+:\d+:\s*", "", message)
    # Also strip lines that are just the module rating or temp filename header
    message = re.sub(r"\*+\s*Module\s+\w+\s*\n?", "", message)
    message = re.sub(r"[\w/\\]+analyzer_\w+\.py", "<source>", message)
    message = re.sub(r"[\w/\\]+tmp\w+\.py", "<source>", message)
    return message.strip()


# ─── Pylint Severity Mapping ──────────────────────────

PYLINT_SEVERITY_MAP = {
    "C": (Severity.INFO, Category.STYLE),        # Convention
    "R": (Severity.INFO, Category.QUALITY),       # Refactor
    "W": (Severity.WARNING, Category.QUALITY),    # Warning
    "E": (Severity.ERROR, Category.SYNTAX),       # Error
    "F": (Severity.CRITICAL, Category.SYNTAX),    # Fatal
}

PYLINT_SUGGESTIONS = {
    "C0114": "Add a module-level docstring: \"\"\"Description of this module.\"\"\"",
    "C0115": "Add a class docstring: \"\"\"Description of this class.\"\"\"",
    "C0116": "Add a function docstring: \"\"\"Description of this function.\"\"\"",
    "C0103": "Use descriptive variable names following snake_case convention.",
    "C0301": "Break long lines at 100 characters or use implicit line continuation.",
    "C0303": "Remove trailing whitespace from the end of the line.",
    "C0304": "Add a newline at the end of the file.",
    "C0411": "Reorder imports: standard library first, then third-party, then local.",
    "W0611": "Remove the unused import or mark it with a comment if needed.",
    "W0612": "Remove the unused variable or prefix with _ to indicate intentional disuse.",
    "W0613": "Remove the unused argument or prefix with _ (e.g., _unused).",
    "W0621": "Rename the variable to avoid shadowing the outer scope name.",
    "W0622": "Avoid redefining Python builtins. Use a different variable name.",
    "E0602": "Define the variable before using it, or check for typos.",
    "E1101": "Verify the object type and check attribute spelling.",
    "R0903": "Consider using a dataclass or named tuple if the class has few methods.",
    "R0913": "Reduce the number of parameters. Consider using a config object.",
    "R0914": "Extract some local variables into helper functions.",
}

PYLINT_TITLES = {
    "C0114": "Missing module docstring",
    "C0115": "Missing class docstring",
    "C0116": "Missing function docstring",
    "C0103": "Non-conforming name",
    "C0301": "Line too long",
    "C0303": "Trailing whitespace",
    "C0304": "Missing final newline",
    "C0411": "Wrong import order",
    "W0611": "Unused import",
    "W0612": "Unused variable",
    "W0613": "Unused argument",
    "W0621": "Variable shadows outer scope",
    "W0622": "Redefining built-in",
    "E0602": "Undefined variable",
    "E1101": "No member in object",
    "R0903": "Too few public methods",
    "R0913": "Too many arguments",
    "R0914": "Too many local variables",
}


def parse_pylint_output(raw_output: str) -> list[Finding]:
    """
    Parse pylint output into individual Finding objects.

    Pylint format: filepath:line:column: CODE (symbol) message
    Example: /tmp/x.py:1:0: C0114 (missing-module-docstring) Missing module docstring
    """
    findings = []

    # Pattern: path:line:col: XNNNN: message (or XNNNN (symbol) message)
    pattern = re.compile(
        r"[^:]+:(\d+):(\d+):\s*([A-Z]\d{4})\s*(?:\([\w-]+\))?\s*(.*)"
    )

    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if not match:
            continue

        line_num = int(match.group(1))
        col_num = int(match.group(2))
        rule_id = match.group(3)
        message = match.group(4).strip()

        # Map severity from rule code prefix
        prefix = rule_id[0]
        severity, category = PYLINT_SEVERITY_MAP.get(
            prefix, (Severity.WARNING, Category.QUALITY)
        )

        title = PYLINT_TITLES.get(rule_id, message[:60])
        suggestion = PYLINT_SUGGESTIONS.get(rule_id)

        findings.append(Finding(
            id=_make_id("pylint", line_num, rule_id, message),
            category=category,
            severity=severity,
            confidence=Confidence.CONFIRMED,
            title=title,
            message=message,
            suggestion=suggestion,
            line=line_num,
            column=col_num,
            rule_id=rule_id,
            source="pylint",
        ))

    return findings


# ─── Flake8 Parser ─────────────────────────────────────

FLAKE8_CATEGORY_MAP = {
    "E": Category.STYLE,       # PEP8 errors
    "W": Category.STYLE,       # PEP8 warnings
    "F": Category.QUALITY,     # PyFlakes
    "C": Category.QUALITY,     # McCabe complexity
    "N": Category.STYLE,       # Naming
}

FLAKE8_SEVERITY_MAP = {
    "E": Severity.WARNING,
    "W": Severity.INFO,
    "F": Severity.ERROR,
    "C": Severity.WARNING,
    "N": Severity.INFO,
}


def parse_flake8_output(raw_output: str) -> list[Finding]:
    """
    Parse flake8 output into individual Finding objects.

    Flake8 format: filepath:line:column: CODE message
    Example: /tmp/x.py:1:1: E302 expected 2 blank lines, found 1
    """
    findings = []

    pattern = re.compile(
        r"[^:]+:(\d+):(\d+):\s*([A-Z]\d+)\s+(.*)"
    )

    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if not match:
            continue

        line_num = int(match.group(1))
        col_num = int(match.group(2))
        rule_id = match.group(3)
        message = match.group(4).strip()

        prefix = rule_id[0]
        category = FLAKE8_CATEGORY_MAP.get(prefix, Category.STYLE)
        severity = FLAKE8_SEVERITY_MAP.get(prefix, Severity.INFO)

        findings.append(Finding(
            id=_make_id("flake8", line_num, rule_id, message),
            category=category,
            severity=severity,
            confidence=Confidence.CONFIRMED,
            title=message[:60],
            message=message,
            suggestion=None,
            line=line_num,
            column=col_num,
            rule_id=rule_id,
            source="flake8",
        ))

    return findings


# ─── Bandit Parser ─────────────────────────────────────

BANDIT_SEVERITY_MAP = {
    "HIGH": Severity.CRITICAL,
    "MEDIUM": Severity.ERROR,
    "LOW": Severity.WARNING,
}


def parse_bandit_output(raw_output: str) -> list[Finding]:
    """
    Parse bandit output into individual Finding objects.

    Bandit default format:
    >> Issue: [BXXX:test_name] message
       Severity: High   Confidence: High
       CWE: CWE-XXX (...)
       Location: filepath:line:col
    """
    findings = []

    # Pattern for issue blocks
    issue_pattern = re.compile(
        r">>\s*Issue:\s*\[([A-Z]\d+):([^\]]+)\]\s*(.*?)(?=\n|$)"
    )
    severity_pattern = re.compile(
        r"Severity:\s*(\w+)\s+Confidence:\s*(\w+)"
    )
    location_pattern = re.compile(
        r"Location:\s*[^:]+:(\d+)(?::(\d+))?"
    )

    # Split into issue blocks
    blocks = raw_output.split(">> Issue:")

    for block in blocks[1:]:  # Skip first empty split
        block = ">> Issue:" + block

        issue_match = issue_pattern.search(block)
        sev_match = severity_pattern.search(block)
        loc_match = location_pattern.search(block)

        if not issue_match:
            continue

        rule_id = issue_match.group(1)
        test_name = issue_match.group(2).strip()
        message = issue_match.group(3).strip()

        sev_text = sev_match.group(1).upper() if sev_match else "MEDIUM"
        severity = BANDIT_SEVERITY_MAP.get(sev_text, Severity.WARNING)

        line_num = int(loc_match.group(1)) if loc_match else None
        col_num = int(loc_match.group(2)) if loc_match and loc_match.group(2) else None

        findings.append(Finding(
            id=_make_id("bandit", line_num, rule_id, message),
            category=Category.SECURITY,
            severity=severity,
            confidence=Confidence.CONFIRMED,
            title=f"Security: {test_name.replace('_', ' ').title()}",
            message=message,
            suggestion="Review this code for security vulnerabilities and apply the recommended fix.",
            line=line_num,
            column=col_num,
            rule_id=rule_id,
            source="bandit",
        ))

    # Fallback: parse simpler line-by-line format
    if not findings and raw_output.strip():
        simple_pattern = re.compile(
            r"[^:]+:(\d+)(?::(\d+))?:\s*(.*)"
        )
        for line in raw_output.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("Run") or line.startswith("Test"):
                continue

            match = simple_pattern.match(line)
            if match:
                findings.append(Finding(
                    id=_make_id("bandit", int(match.group(1)), "B000", match.group(3)),
                    category=Category.SECURITY,
                    severity=Severity.WARNING,
                    confidence=Confidence.HEURISTIC,
                    title="Security finding",
                    message=_strip_temp_path(match.group(3)),
                    line=int(match.group(1)),
                    rule_id="B000",
                    source="bandit",
                ))

    return findings


# ─── MyPy Parser ───────────────────────────────────────

def parse_mypy_output(raw_output: str) -> list[Finding]:
    """
    Parse mypy output into individual Finding objects.

    MyPy format: filepath:line: error: message [error-code]
    Example: /tmp/x.py:5: error: Incompatible types [assignment]
    """
    findings = []

    # Skip "Success" output
    if "success" in raw_output.lower():
        return findings

    pattern = re.compile(
        r"[^:]+:(\d+):\s*(error|warning|note):\s*(.*?)(?:\s*\[(\w[\w-]*)\])?\s*$"
    )

    for line in raw_output.splitlines():
        line = line.strip()
        if not line or line.startswith("Found"):
            continue

        match = pattern.match(line)
        if not match:
            continue

        line_num = int(match.group(1))
        level = match.group(2)
        message = match.group(3).strip()
        error_code = match.group(4) or ""

        severity_map = {
            "error": Severity.ERROR,
            "warning": Severity.WARNING,
            "note": Severity.INFO,
        }
        severity = severity_map.get(level, Severity.WARNING)

        findings.append(Finding(
            id=_make_id("mypy", line_num, error_code, message),
            category=Category.TYPE,
            severity=severity,
            confidence=Confidence.CONFIRMED,
            title=f"Type error: {message[:50]}",
            message=_strip_temp_path(message),
            suggestion="Add type annotations or fix the type mismatch.",
            line=line_num,
            rule_id=error_code,
            source="mypy",
        ))

    return findings


# ─── AST Parser ────────────────────────────────────────

def parse_ast_error(error: SyntaxError) -> Finding:
    """Convert a Python SyntaxError into a structured Finding."""
    message = str(error.msg) if error.msg else str(error)

    return Finding(
        id=_make_id("ast", error.lineno, "SyntaxError", message),
        category=Category.SYNTAX,
        severity=Severity.ERROR,
        confidence=Confidence.CONFIRMED,
        title="Syntax error",
        message=message,
        suggestion="Fix the syntax error to allow further analysis.",
        line=error.lineno,
        column=error.offset,
        rule_id="SyntaxError",
        source="ast",
    )


# ─── Dependency Parser ─────────────────────────────────

def parse_pip_audit_output(raw_output: str) -> list[Finding]:
    """
    Parse pip-audit output into structured findings.

    pip-audit format:
    Name    Version ID              Fix Versions
    ------- ------- --------------- ------------
    package 1.0.0   PYSEC-2024-XXX  1.0.1
    """
    findings = []

    if not raw_output or not raw_output.strip():
        return findings

    # Skip header lines
    lines = raw_output.strip().splitlines()
    data_started = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("---"):
            data_started = True
            continue
        if not data_started:
            continue

        parts = line.split()
        if len(parts) >= 3:
            package = parts[0]
            version = parts[1]
            vuln_id = parts[2] if len(parts) > 2 else ""
            fix_version = parts[3] if len(parts) > 3 else ""

            findings.append(Finding(
                id=_make_id("pip-audit", None, vuln_id, package),
                category=Category.DEPENDENCY,
                severity=Severity.ERROR,
                confidence=Confidence.CONFIRMED,
                title=f"Vulnerable package: {package}",
                message=f"Package '{package}' version {version} has known vulnerability {vuln_id}.",
                suggestion=f"Upgrade to version {fix_version}." if fix_version else "Check for available updates.",
                rule_id=vuln_id,
                source="pip-audit",
            ))

    # Fallback for unstructured output
    if not findings and "No known vulnerabilities found" not in raw_output:
        findings.append(Finding(
            id=_make_id("pip-audit", None, "DEP001", raw_output[:50]),
            category=Category.DEPENDENCY,
            severity=Severity.WARNING,
            confidence=Confidence.HEURISTIC,
            title="Dependency scan results",
            message=_strip_temp_path(raw_output[:500]),
            source="pip-audit",
        ))

    return findings
