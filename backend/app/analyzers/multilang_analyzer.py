"""
Java and C++ analyzers — preserved cross-language checks from original app.py.

These use the same rule-based checks as the original (balanced symbols,
missing semicolons, unclosed quotes, structure checks) but output
structured Finding objects instead of raw dicts.
"""

import re
import hashlib
from .base import BaseAnalyzer
from ..models.responses import Finding, Severity, Category, Confidence


def _make_id(source: str, line: int | None, rule_id: str, message: str) -> str:
    raw = f"{source}:{line or 0}:{rule_id}:{message[:80]}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]


# ─── Shared Cross-Language Checks ──────────────────────

def check_balanced_symbols(code: str) -> Finding | None:
    """
    Check for unmatched brackets, parens, braces.
    Preserved from original app.py lines 208-243.
    """
    stack = []
    pairs = {")": "(", "}": "{", "]": "["}
    opening = set("({[")
    closing = set(")}]")

    for line_no, line in enumerate(code.splitlines(), start=1):
        for char in line:
            if char in opening:
                stack.append((char, line_no))
            elif char in closing:
                if not stack or stack[-1][0] != pairs[char]:
                    return Finding(
                        id=_make_id("rule-parser", line_no, "SYM001", f"Unmatched {char}"),
                        category=Category.SYNTAX,
                        severity=Severity.ERROR,
                        confidence=Confidence.CONFIRMED,
                        title=f"Unmatched closing symbol '{char}'",
                        message=f"Unmatched closing symbol '{char}' detected.",
                        suggestion="Add the matching opening symbol or remove this closing symbol.",
                        line=line_no,
                        rule_id="SYM001",
                        source="rule-parser",
                    )
                stack.pop()

    if stack:
        symbol, line_no = stack[-1]
        return Finding(
            id=_make_id("rule-parser", line_no, "SYM002", f"Unclosed {symbol}"),
            category=Category.SYNTAX,
            severity=Severity.ERROR,
            confidence=Confidence.CONFIRMED,
            title=f"Unclosed opening symbol '{symbol}'",
            message=f"Unclosed opening symbol '{symbol}' detected.",
            suggestion="Add the matching closing symbol.",
            line=line_no,
            rule_id="SYM002",
            source="rule-parser",
        )

    return None


def check_unclosed_quotes(code: str) -> list[Finding]:
    """
    Check for unclosed string quotes on each line.
    Preserved from original app.py lines 202-205.
    """
    findings = []
    for line_no, line in enumerate(code.splitlines(), start=1):
        double_quotes = line.count('"') - line.count('\\"')
        single_quotes = line.count("'") - line.count("\\'")
        if double_quotes % 2 != 0 or single_quotes % 2 != 0:
            findings.append(Finding(
                id=_make_id("rule-parser", line_no, "STR001", "Unclosed string"),
                category=Category.SYNTAX,
                severity=Severity.ERROR,
                confidence=Confidence.HEURISTIC,
                title="Unclosed string literal",
                message="Unclosed string quote detected.",
                suggestion="Close the string with a matching quote character.",
                line=line_no,
                rule_id="STR001",
                source="rule-parser",
            ))
    return findings


def check_missing_semicolons(code: str, language: str) -> list[Finding]:
    """
    Check for missing semicolons in Java/C++ code.
    Preserved from original app.py lines 246-306.
    """
    findings = []
    skip_starters = (
        "if", "for", "while", "switch", "class", "public class",
        "else", "try", "catch", "finally", "do", "#include", "using namespace"
    )

    if language == "java":
        indicators = [
            "System.out.print", "=", "return", "new ",
            "int ", "String ", "double ", "float ", "boolean "
        ]
    else:
        indicators = [
            "cout", "cin", "=", "return",
            "int ", "string ", "double ", "float ", "bool "
        ]

    for line_no, raw_line in enumerate(code.splitlines(), start=1):
        line = raw_line.strip()
        
        # Strip inline comments, being careful not to strip URLs like http:// or https://
        line = re.sub(r'(?<!:)//.*$', '', line).strip()
        line = re.sub(r'/\*.*\*/', '', line).strip()
        
        if not line or line.startswith("*"):
            continue
        # If line ends with a continuation character, ignore it
        if line[-1] in "{};=+-*/|&,([":
            continue
        if any(line.startswith(kw) for kw in skip_starters):
            continue
        if any(token in line for token in indicators):
            findings.append(Finding(
                id=_make_id(f"{language}-parser", line_no, "SEMI001", "Missing semicolon"),
                category=Category.SYNTAX,
                severity=Severity.WARNING,
                confidence=Confidence.HEURISTIC,
                title="Possible missing semicolon",
                message="Possible missing semicolon at end of statement.",
                suggestion="Add a semicolon (;) at the end of this statement.",
                line=line_no,
                rule_id="SEMI001",
                source=f"{language}-parser",
            ))

    return findings


def check_cpp_security(code: str) -> list[Finding]:
    findings = []
    
    # Check for unsafe functions (buffer overflows)
    unsafe_funcs = {
        "strcpy": "strcpy() does not check buffer bounds. Use strncpy() or std::string.",
        "sprintf": "sprintf() does not check buffer bounds. Use snprintf() or std::stringstream.",
        "gets": "gets() is extremely dangerous and removed from modern C++. Use std::cin.getline() or fgets().",
        "strcat": "strcat() does not check buffer bounds. Use strncat() or std::string."
    }
    
    # Check for memory management issues
    new_count = 0
    delete_count = 0
    malloc_count = 0
    free_count = 0
    
    for line_no, line in enumerate(code.splitlines(), start=1):
        clean_line = line.split("//")[0].strip()
        if not clean_line: continue
        
        # Unsafe functions
        for func, msg in unsafe_funcs.items():
            if re.search(r'\b' + func + r'\s*\(', clean_line):
                findings.append(Finding(
                    id=_make_id("cpp-sec", line_no, "SEC001", func),
                    category=Category.SECURITY,
                    severity=Severity.CRITICAL,
                    confidence=Confidence.CONFIRMED,
                    title="Buffer Overflow Risk",
                    message=msg,
                    suggestion="Replace with a safer alternative.",
                    line=line_no,
                    rule_id="SEC001",
                    source="cpp-sec-scanner",
                ))
                
        # Hardcoded Secrets
        if re.search(r'(?i)(password|secret|api_key|token|license_key)\s*=\s*["\'][^"\']+["\']', clean_line):
            findings.append(Finding(
                id=_make_id("cpp-sec", line_no, "SEC006", "Secret"),
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                confidence=Confidence.HEURISTIC,
                title="Hardcoded Secret",
                message="A secret, password, or API key appears to be hardcoded.",
                suggestion="Use environment variables or a secure vault.",
                line=line_no,
                rule_id="SEC006",
                source="cpp-sec-scanner",
            ))
                
        # Basic counting for memory leaks
        if re.search(r'\bnew\b', clean_line): new_count += 1
        if re.search(r'\bdelete\b', clean_line): delete_count += 1
        if re.search(r'\bmalloc\b', clean_line): malloc_count += 1
        if re.search(r'\bfree\b', clean_line): free_count += 1
        
        # Use after free or dangling pointer pattern (basic heuristic: delete x; x = ...)
        if re.search(r'\bdelete\b\s+[\w\-\>]+', clean_line):
            findings.append(Finding(
                id=_make_id("cpp-sec", line_no, "MEM001", "Dangling Pointer"),
                category=Category.QUALITY,
                severity=Severity.WARNING,
                confidence=Confidence.HEURISTIC,
                title="Potential Dangling Pointer",
                message="Memory freed but pointer not explicitly set to nullptr immediately.",
                suggestion="Set pointer to nullptr after delete to prevent use-after-free bugs.",
                line=line_no,
                rule_id="MEM001",
                source="cpp-sec-scanner",
            ))

    if new_count > delete_count:
        findings.append(Finding(
            id=_make_id("cpp-sec", None, "MEM002", "Memory Leak new"),
            category=Category.QUALITY,
            severity=Severity.ERROR,
            confidence=Confidence.HEURISTIC,
            title="Potential Memory Leak",
            message=f"Found {new_count} 'new' allocations but only {delete_count} 'delete' calls.",
            suggestion="Ensure every 'new' has a corresponding 'delete', or use smart pointers (std::unique_ptr).",
            rule_id="MEM002",
            source="cpp-sec-scanner",
        ))
        
    if malloc_count > free_count:
        findings.append(Finding(
            id=_make_id("cpp-sec", None, "MEM003", "Memory Leak malloc"),
            category=Category.QUALITY,
            severity=Severity.ERROR,
            confidence=Confidence.HEURISTIC,
            title="Potential Memory Leak",
            message=f"Found {malloc_count} 'malloc' allocations but only {free_count} 'free' calls.",
            suggestion="Ensure every 'malloc' has a corresponding 'free'.",
            rule_id="MEM003",
            source="cpp-sec-scanner",
        ))

    return findings

def check_java_security(code: str) -> list[Finding]:
    findings = []
    
    for line_no, line in enumerate(code.splitlines(), start=1):
        clean_line = line.split("//")[0].strip()
        if not clean_line: continue
        
        # SQL Injection
        if re.search(r'(?i)SELECT.*FROM.*WHERE.*\+\s*\w+', clean_line) or re.search(r'(?i)UPDATE.*SET.*\+\s*\w+', clean_line):
            findings.append(Finding(
                id=_make_id("java-sec", line_no, "SEC002", "SQLi"),
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                confidence=Confidence.HEURISTIC,
                title="SQL Injection Risk",
                message="Dynamic SQL query construction detected.",
                suggestion="Use PreparedStatement or parameterized queries.",
                line=line_no,
                rule_id="SEC002",
                source="java-sec-scanner",
            ))
            
        # Hardcoded secrets
        if re.search(r'(?i)(password|secret|api_key|token|license_key)\s*=\s*["\'][^"\']+["\']', clean_line):
            findings.append(Finding(
                id=_make_id("java-sec", line_no, "SEC003", "Secret"),
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                confidence=Confidence.HEURISTIC,
                title="Hardcoded Secret",
                message="A secret, password, or API key appears to be hardcoded in the source.",
                suggestion="Use environment variables or a secure vault.",
                line=line_no,
                rule_id="SEC003",
                source="java-sec-scanner",
            ))
            
        # Predictable JWT
        if "Jwts.builder().setSigningKey" in clean_line and "getBytes()" in clean_line:
            findings.append(Finding(
                id=_make_id("java-sec", line_no, "SEC006", "WeakJWT"),
                category=Category.SECURITY,
                severity=Severity.ERROR,
                confidence=Confidence.HEURISTIC,
                title="Weak JWT Signing Key",
                message="Using a hardcoded or predictable string as a JWT signing key.",
                suggestion="Use a secure, rotating key from a KMS or environment variable.",
                line=line_no,
                rule_id="SEC006",
                source="java-sec-scanner",
            ))
            
        # Weak Hashing
        if re.search(r'MessageDigest\.getInstance\(\s*["\'](MD5|SHA-1)["\']\s*\)', clean_line):
            findings.append(Finding(
                id=_make_id("java-sec", line_no, "SEC004", "WeakHash"),
                category=Category.SECURITY,
                severity=Severity.ERROR,
                confidence=Confidence.CONFIRMED,
                title="Weak Cryptographic Hash",
                message="MD5 or SHA-1 is cryptographically weak.",
                suggestion="Use SHA-256, SHA-3, or bcrypt/Argon2 for passwords.",
                line=line_no,
                rule_id="SEC004",
                source="java-sec-scanner",
            ))
            
        # Command Injection
        if re.search(r'Runtime\.getRuntime\(\)\.exec\(', clean_line):
            findings.append(Finding(
                id=_make_id("java-sec", line_no, "SEC005", "CmdInj"),
                category=Category.SECURITY,
                severity=Severity.ERROR,
                confidence=Confidence.HEURISTIC,
                title="Command Injection Risk",
                message="Execution of OS commands can lead to command injection.",
                suggestion="Use ProcessBuilder and avoid passing user input directly.",
                line=line_no,
                rule_id="SEC005",
                source="java-sec-scanner",
            ))

    return findings

def check_java_quality(code: str) -> list[Finding]:
    findings = []
    
    for line_no, line in enumerate(code.splitlines(), start=1):
        clean_line = line.split("//")[0].strip()
        if not clean_line: continue
        
        # Swallowed exceptions
        if re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', clean_line):
            findings.append(Finding(
                id=_make_id("java-qual", line_no, "QUAL001", "Swallow"),
                category=Category.QUALITY,
                severity=Severity.WARNING,
                confidence=Confidence.HEURISTIC,
                title="Swallowed Exception",
                message="Exception is caught but silently swallowed.",
                suggestion="Log the exception or re-throw it.",
                line=line_no,
                rule_id="QUAL001",
                source="java-qual-scanner",
            ))
            
        # Single un-pooled database connection
        if "DriverManager.getConnection" in clean_line and "Connection" in clean_line:
            findings.append(Finding(
                id=_make_id("java-qual", line_no, "QUAL002", "NoPool"),
                category=Category.QUALITY,
                severity=Severity.WARNING,
                confidence=Confidence.HEURISTIC,
                title="Un-pooled Database Connection",
                message="Connection created directly without a connection pool.",
                suggestion="Use HikariCP or similar connection pool.",
                line=line_no,
                rule_id="QUAL002",
                source="java-qual-scanner",
            ))
            
        # NullPointer risks with object wrappers
        if re.search(r'\b(Integer|Double|Float)\s+\w+\s*=', clean_line):
            findings.append(Finding(
                id=_make_id("java-qual", line_no, "QUAL003", "NullPtr"),
                category=Category.QUALITY,
                severity=Severity.INFO,
                confidence=Confidence.HEURISTIC,
                title="NullPointerException Risk",
                message="Object wrapper used where primitives might be safer due to null risks.",
                suggestion="Ensure null checks are in place before auto-unboxing.",
                line=line_no,
                rule_id="QUAL003",
                source="java-qual-scanner",
            ))

    return findings

def check_java_performance(code: str) -> list[Finding]:
    findings = []
    
    for line_no, line in enumerate(code.splitlines(), start=1):
        clean_line = line.split("//")[0].strip()
        if not clean_line: continue
        
        # Fetching ALL data into memory without pagination
        if re.search(r'\.findAll\(\)(?!.*Pageable)', clean_line):
            findings.append(Finding(
                id=_make_id("java-perf", line_no, "PERF001", "FetchAll"),
                category=Category.PERFORMANCE,
                severity=Severity.ERROR,
                confidence=Confidence.HEURISTIC,
                title="Memory Issue for Large Datasets",
                message="Fetching all database records into memory without pagination.",
                suggestion="Use pagination (PageRequest) to limit result sets.",
                line=line_no,
                rule_id="PERF001",
                source="java-perf-scanner",
            ))
            
        # Loads ALL then filters in memory
        if re.search(r'\.findAll\(\)\.stream\(\)\.filter\(', clean_line):
            findings.append(Finding(
                id=_make_id("java-perf", line_no, "PERF002", "FilterMem"),
                category=Category.PERFORMANCE,
                severity=Severity.ERROR,
                confidence=Confidence.CONFIRMED,
                title="Inefficient In-Memory Filtering",
                message="Loads all records from the database and then filters in memory.",
                suggestion="Filter records directly in the SQL query using WHERE clauses.",
                line=line_no,
                rule_id="PERF002",
                source="java-perf-scanner",
            ))
            
        # Unbounded in-memory caches
        if re.search(r'new\s+(HashMap|ConcurrentHashMap).*<\s*\w+\s*,\s*\w+\s*>', clean_line) and "cache" in clean_line.lower():
            findings.append(Finding(
                id=_make_id("java-perf", line_no, "PERF003", "NoTTL"),
                category=Category.PERFORMANCE,
                severity=Severity.WARNING,
                confidence=Confidence.HEURISTIC,
                title="Unbounded In-Memory Cache",
                message="In-memory cache instantiated with no explicit eviction policy or TTL.",
                suggestion="Use a caching library like Caffeine or Guava with maximum size and TTL.",
                line=line_no,
                rule_id="PERF003",
                source="java-perf-scanner",
            ))

    return findings

# ─── Java Analyzer ─────────────────────────────────────

class JavaAnalyzer(BaseAnalyzer):
    """Analyzer for Java source code using rule-based checks."""

    def quick_analyze(self, code: str) -> list[Finding]:
        return self._run_checks(code)

    def full_analyze(self, code: str) -> list[Finding]:
        return self._run_checks(code)

    def get_tools_used(self) -> list[str]:
        return ["java-rule-parser"]

    def _run_checks(self, code: str) -> list[Finding]:
        findings: list[Finding] = []

        if not code.strip():
            findings.append(Finding(
                id=_make_id("java-parser", None, "INP001", "No code"),
                category=Category.STRUCTURE,
                severity=Severity.WARNING,
                confidence=Confidence.CONFIRMED,
                title="No code provided",
                message="No code provided for analysis.",
                line=None,
                rule_id="INP001",
                source="java-parser",
            ))
            return findings

        # Balanced symbols
        sym = check_balanced_symbols(code)
        if sym:
            findings.append(sym)

        # Unclosed quotes
        findings.extend(check_unclosed_quotes(code))

        # Missing semicolons
        findings.extend(check_missing_semicolons(code, "java"))

        # Security/Vulnerability checks
        findings.extend(check_java_security(code))
        
        # Quality and Performance checks
        findings.extend(check_java_quality(code))
        findings.extend(check_java_performance(code))

        # Structure checks (preserved from original)
        if "class " not in code:
            findings.append(Finding(
                id=_make_id("java-parser", None, "JAVA001", "No class"),
                category=Category.STRUCTURE,
                severity=Severity.WARNING,
                confidence=Confidence.HEURISTIC,
                title="Missing class declaration",
                message="Java code usually requires a class declaration.",
                suggestion="Wrap your code in a class: public class Main { ... }",
                rule_id="JAVA001",
                source="java-parser",
            ))

        if "public static void main" not in code:
            findings.append(Finding(
                id=_make_id("java-parser", None, "JAVA002", "No main"),
                category=Category.STRUCTURE,
                severity=Severity.INFO,
                confidence=Confidence.HEURISTIC,
                title="No main method",
                message="No main method detected. A runnable Java program usually contains public static void main.",
                suggestion="Add: public static void main(String[] args) { ... }",
                rule_id="JAVA002",
                source="java-parser",
            ))

        return findings


# ─── C++ Analyzer ──────────────────────────────────────

class CppAnalyzer(BaseAnalyzer):
    """Analyzer for C++ source code using rule-based checks."""

    def quick_analyze(self, code: str) -> list[Finding]:
        return self._run_checks(code)

    def full_analyze(self, code: str) -> list[Finding]:
        return self._run_checks(code)

    def get_tools_used(self) -> list[str]:
        return ["cpp-rule-parser"]

    def _run_checks(self, code: str) -> list[Finding]:
        findings: list[Finding] = []

        if not code.strip():
            findings.append(Finding(
                id=_make_id("cpp-parser", None, "INP001", "No code"),
                category=Category.STRUCTURE,
                severity=Severity.WARNING,
                confidence=Confidence.CONFIRMED,
                title="No code provided",
                message="No code provided for analysis.",
                rule_id="INP001",
                source="cpp-parser",
            ))
            return findings

        # Balanced symbols
        sym = check_balanced_symbols(code)
        if sym:
            findings.append(sym)

        # Unclosed quotes
        findings.extend(check_unclosed_quotes(code))

        # Missing semicolons
        findings.extend(check_missing_semicolons(code, "cpp"))

        # Security/Vulnerability checks
        findings.extend(check_cpp_security(code))

        # Structure checks (preserved from original)
        if "int main" not in code:
            findings.append(Finding(
                id=_make_id("cpp-parser", None, "CPP001", "No main"),
                category=Category.STRUCTURE,
                severity=Severity.WARNING,
                confidence=Confidence.HEURISTIC,
                title="No main function",
                message="No int main() function detected.",
                suggestion="Add: int main() { ... return 0; }",
                rule_id="CPP001",
                source="cpp-parser",
            ))

        if "#include" not in code:
            findings.append(Finding(
                id=_make_id("cpp-parser", None, "CPP002", "No include"),
                category=Category.STRUCTURE,
                severity=Severity.INFO,
                confidence=Confidence.HEURISTIC,
                title="No #include statements",
                message="No #include statement detected. Many C++ programs include standard libraries.",
                suggestion="Add: #include <iostream> or other headers as needed.",
                rule_id="CPP002",
                source="cpp-parser",
            ))

        if "cout" in code and "iostream" not in code:
            findings.append(Finding(
                id=_make_id("cpp-parser", None, "CPP003", "Missing iostream"),
                category=Category.DEPENDENCY,
                severity=Severity.WARNING,
                confidence=Confidence.CONFIRMED,
                title="Missing <iostream> include",
                message="cout is used but <iostream> include was not detected.",
                suggestion="Add: #include <iostream>",
                rule_id="CPP003",
                source="cpp-parser",
            ))

        return findings
