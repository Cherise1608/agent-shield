"""Check for audit logging and traceability in agent systems."""
import re
from pathlib import Path

LOGGING_PATTERNS = [
    (r'(?i)import\s+logging', "Python logging module", 2),
    (r'(?i)from\s+logging\s+import', "Python logging module", 2),
    (r'(?i)structlog|structured.?log', "Structured logging library", 3),
    (r'(?i)winston|pino|bunyan', "Node.js structured logger", 3),
    (r'(?i)logger\.(info|warning|error|debug|critical)', "Logger usage", 1),
    (r'(?i)console\.(log|warn|error|info)', "Console logging (basic)", 1),
]

AUDIT_PATTERNS = [
    (r'(?i)audit[_\-]?log|audit[_\-]?trail', "Audit trail reference", 4),
    (r'(?i)trace[_\-]?id|correlation[_\-]?id|request[_\-]?id', "Trace/correlation ID", 3),
    (r'(?i)decision[_\-]?log|agent[_\-]?log', "Agent decision logging", 4),
    (r'(?i)langfuse|langsmith|agentops|phoenix', "Observability platform", 3),
    (r'(?i)opentelemetry|otel', "OpenTelemetry tracing", 3),
]

IO_LOGGING_PATTERNS = [
    (r'(?i)log.*input|log.*prompt|log.*request', "Input logging", 2),
    (r'(?i)log.*output|log.*response|log.*result', "Output logging", 2),
    (r'(?i)log.*tool[_\-]?call|log.*function[_\-]?call', "Tool call logging", 2),
]

def check_audit_logging(project_path: Path, files: list[Path]) -> dict:
    """Check for audit logging and traceability. Max 20 points."""
    score = 0
    findings = []
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}

    has_basic_logging = False
    has_structured_logging = False
    has_audit_trail = False
    has_trace_ids = False
    has_io_logging = False
    has_observability = False

    for f in files:
        if f.suffix not in code_extensions:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        for pattern, name, points in LOGGING_PATTERNS:
            if re.search(pattern, content):
                if "structured" in name.lower() or name in {"Node.js structured logger"}:
                    has_structured_logging = True
                else:
                    has_basic_logging = True

        for pattern, name, points in AUDIT_PATTERNS:
            if re.search(pattern, content):
                if "trace" in name.lower() or "correlation" in name.lower():
                    has_trace_ids = True
                elif "observability" in name.lower():
                    has_observability = True
                else:
                    has_audit_trail = True

        for pattern, name, points in IO_LOGGING_PATTERNS:
            if re.search(pattern, content):
                has_io_logging = True

    if has_basic_logging:
        score += 3
        findings.append({
            "severity": "pass",
            "category": "audit",
            "title": "Basic logging detected",
            "detail": "Found logging module usage.",
        })
    else:
        findings.append({
            "severity": "critical",
            "category": "audit",
            "title": "No logging detected",
            "detail": "No logging framework or logger usage found in code.",
            "fix": "Add structured logging (structlog for Python, pino for Node.js).",
            "articles": ["EU AI Act Art. 12", "EU AI Act Art. 19"],
        })

    if has_structured_logging:
        score += 3
        findings.append({
            "severity": "pass",
            "category": "audit",
            "title": "Structured logging detected",
            "detail": "Found structured logging library (structlog, winston, pino, or similar).",
        })

    if has_audit_trail:
        score += 5
        findings.append({
            "severity": "pass",
            "category": "audit",
            "title": "Audit trail pattern detected",
            "detail": "Found audit log or decision logging patterns.",
        })
    else:
        findings.append({
            "severity": "critical",
            "category": "audit",
            "title": "No audit trail detected",
            "detail": "No structured audit trail or decision logging found for agent actions.",
            "fix": "Add decision logging middleware that captures: input, reasoning, tool calls, output, timestamp, and session ID.",
            "articles": ["EU AI Act Art. 12", "EU AI Act Art. 18"],
        })

    if has_trace_ids:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "audit",
            "title": "Trace/correlation IDs detected",
            "detail": "Found trace_id, correlation_id, or request_id patterns.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "audit",
            "title": "No trace IDs detected",
            "detail": "No correlation or trace ID patterns found. Agent actions cannot be linked across calls.",
            "fix": "Add a unique trace_id to every agent invocation for end-to-end traceability.",
            "articles": ["EU AI Act Art. 12"],
        })

    if has_io_logging:
        score += 3
        findings.append({
            "severity": "pass",
            "category": "audit",
            "title": "Input/output logging detected",
            "detail": "Found patterns for logging agent inputs and outputs.",
        })

    if has_observability:
        score += 2
        findings.append({
            "severity": "pass",
            "category": "audit",
            "title": "Observability platform integration detected",
            "detail": "Found integration with Langfuse, LangSmith, AgentOps, or OpenTelemetry.",
        })

    return {
        "name": "Audit & Logging",
        "icon": "📋",
        "score": min(score, 20),
        "max_score": 20,
        "findings": findings,
    }
