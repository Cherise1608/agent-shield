"""Check for robust error handling and graceful degradation."""
import re
from pathlib import Path

BARE_EXCEPT = re.compile(r'^\s*except\s*:', re.MULTILINE)
BROAD_EXCEPT = re.compile(r'except\s+Exception\s*:')

FALLBACK_PATTERNS = [
    (r'(?i)fallback|graceful[_\-]?degrad', "Fallback / graceful degradation"),
    (r'(?i)circuit[_\-]?breaker|CircuitBreaker', "Circuit breaker"),
    (r'(?i)retry|backoff|Retry|tenacity', "Retry / backoff"),
    (r'(?i)timeout|Timeout', "Timeout handling"),
]

BOUNDARY_PATTERNS = [
    (r'(?i)max[_\-]?(retries|attempts|iterations|steps|tokens|loops)', "Loop / resource bounds"),
    (r'(?i)rate[_\-]?limit|throttle', "Rate limiting"),
    (r'(?i)input[_\-]?valid|validate[_\-]?input|sanitiz', "Input validation / sanitisation"),
]

ERROR_REPORTING_PATTERNS = [
    (r'(?i)sentry|bugsnag|rollbar|airbrake|datadog', "Error reporting service"),
    (r'(?i)error[_\-]?handler|exception[_\-]?handler', "Centralised error handler"),
]


def check_error_handling(project_path: Path, files: list[Path]) -> dict:
    """Check for robust error handling and graceful degradation. Max 15 points."""
    score = 0
    findings = []

    bare_count = 0
    broad_count = 0
    py_files = 0
    has_fallback = False
    has_boundaries = False
    has_error_reporting = False

    for f in files:
        if f.suffix != ".py":
            continue
        py_files += 1
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        bare_count += len(BARE_EXCEPT.findall(content))
        broad_count += len(BROAD_EXCEPT.findall(content))

        for pattern, name in FALLBACK_PATTERNS:
            if re.search(pattern, content):
                has_fallback = True

        for pattern, name in BOUNDARY_PATTERNS:
            if re.search(pattern, content):
                has_boundaries = True

        for pattern, name in ERROR_REPORTING_PATTERNS:
            if re.search(pattern, content):
                has_error_reporting = True

    if py_files == 0:
        return {
            "name": "Error Handling",
            "icon": "⚠️",
            "score": 0,
            "max_score": 15,
            "findings": [{
                "severity": "warning",
                "category": "error_handling",
                "title": "No Python files to evaluate",
                "detail": "No .py files found in the project.",
            }],
        }

    # Bare excepts
    if bare_count == 0:
        score += 3
        findings.append({
            "severity": "pass",
            "category": "error_handling",
            "title": "No bare except clauses",
            "detail": "No bare 'except:' found — errors are caught specifically.",
        })
    else:
        findings.append({
            "severity": "critical",
            "category": "error_handling",
            "title": f"{bare_count} bare except clause(s)",
            "detail": "Bare 'except:' silently swallows all errors including KeyboardInterrupt.",
            "fix": "Replace bare except with specific exception types.",
            "articles": ["EU AI Act Art. 15"],
        })

    # Broad excepts
    if broad_count > 3:
        findings.append({
            "severity": "warning",
            "category": "error_handling",
            "title": f"{broad_count} broad 'except Exception' clause(s)",
            "detail": "Excessive broad exception handling reduces observability.",
            "fix": "Catch specific exceptions. Use broad catches only at top-level boundaries.",
            "articles": ["EU AI Act Art. 15"],
        })

    # Fallback / retry
    if has_fallback:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "error_handling",
            "title": "Fallback / retry patterns detected",
            "detail": "Found circuit breaker, retry, backoff, or graceful degradation logic.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "error_handling",
            "title": "No fallback / retry patterns",
            "detail": "No circuit breaker, retry, or graceful degradation patterns found.",
            "fix": "Add retry with exponential backoff for external calls. Add a circuit breaker for downstream services.",
            "articles": ["EU AI Act Art. 15"],
        })

    # Boundaries
    if has_boundaries:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "error_handling",
            "title": "Resource boundaries detected",
            "detail": "Found max retries, rate limits, input validation, or loop bounds.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "error_handling",
            "title": "No resource boundaries detected",
            "detail": "No max iterations, rate limits, or input validation found.",
            "fix": "Add explicit bounds on loops, retries, and token usage to prevent runaway agents.",
            "articles": ["EU AI Act Art. 15"],
        })

    # Error reporting
    if has_error_reporting:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "error_handling",
            "title": "Error reporting integration detected",
            "detail": "Found Sentry, Datadog, or centralised error handler.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "error_handling",
            "title": "No error reporting integration",
            "detail": "No centralised error reporting service found.",
            "fix": "Add an error reporting service (Sentry, Datadog) for production observability.",
            "articles": ["EU AI Act Art. 12"],
        })

    return {
        "name": "Error Handling",
        "icon": "⚠️",
        "score": min(score, 15),
        "max_score": 15,
        "findings": findings,
    }
