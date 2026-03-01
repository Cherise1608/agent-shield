"""Check for missing accountability ownership (EU AI Act Article 22 + GDPR Article 5(2))."""
import re
from pathlib import Path

# Agent/tool config files that should declare an owner
CONFIG_EXTENSIONS = {".yaml", ".yml", ".toml", ".json"}
OWNER_PATTERNS = [
    r'(?i)["\']?(?:owner|responsible[_\-]?party|contact|maintainer|accountable)["\']?\s*[:=]',
]

# Multi-agent orchestration patterns
MULTI_AGENT_PATTERNS = [
    r'(?i)(?:agent|tool)[_\-]?chain',
    r'(?i)(?:multi[_\-]?agent|agent[_\-]?orchestrat|agent[_\-]?pipeline)',
    r'(?i)(?:run[_\-]?agent|call[_\-]?agent|invoke[_\-]?agent|spawn[_\-]?agent)',
    r'(?i)(?:crew|swarm|graph)\s*[\(\{=]',
    r'(?i)agent\s*\(\s*["\']',
    r'(?i)tools?\s*=\s*\[.*(?:agent|tool)',
]

ESCALATION_PATTERNS = [
    r'(?i)escalat(?:e|ion)',
    r'(?i)fallback[_\-]?handler',
    r'(?i)on[_\-]?(?:error|failure)[_\-]?(?:escalate|notify|alert)',
    r'(?i)human[_\-]?fallback',
]

# Silent error handling on agent paths
SILENT_ERROR_PATTERNS = [
    (r'except\s*:\s*\n\s*pass', "Bare except with pass"),
    (r'except\s+\w+.*:\s*\n\s*pass', "Typed except with pass"),
    (r'except.*:\s*\n\s*logger?\.debug\(', "Exception logged at debug level only"),
    (r'except.*:\s*\n\s*#\s*(?:todo|ignore|skip)', "Exception silenced with comment"),
]

# Output validation patterns (presence = good)
VALIDATION_PATTERNS = [
    r'(?i)(?:schema|pydantic|validate|validator|jsonschema)',
    r'(?i)(?:type[_\-]?check|isinstance|assert\s+isinstance)',
    r'(?i)(?:bounds[_\-]?check|range[_\-]?check|clamp|min\(.*max\()',
    r'(?i)(?:sanitize|escape|clean|strip[_\-]?tags)',
    r'(?i)(?:output[_\-]?valid|response[_\-]?valid|result[_\-]?valid)',
]

# Audit trail patterns (presence = good)
AUDIT_TRAIL_PATTERNS = [
    r'(?i)(?:timestamp|created[_\-]?at|logged[_\-]?at)',
    r'(?i)(?:agent[_\-]?id|actor[_\-]?id|user[_\-]?id)',
    r'(?i)(?:input[_\-]?hash|output[_\-]?hash|content[_\-]?hash)',
    r'(?i)(?:decision[_\-]?rationale|reasoning|justification|explanation)',
    r'(?i)(?:audit[_\-]?log|audit[_\-]?trail|audit[_\-]?record|audit[_\-]?entry)',
]


def check_art22_accountability(project_path: Path, files: list[Path]) -> dict:
    """Check for missing accountability ownership. Max 15 points."""
    score = 15
    findings = []
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}

    has_owner_field = False
    has_multi_agent = False
    has_escalation = False
    silent_error_hits = []
    has_output_validation = False
    audit_trail_count = 0

    # --- Scan config files for owner/responsible_party ---
    for f in files:
        if f.suffix not in CONFIG_EXTENSIONS:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue
        for pattern in OWNER_PATTERNS:
            if re.search(pattern, content):
                has_owner_field = True
                break

    # --- Scan code files ---
    for f in files:
        if f.suffix not in code_extensions:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        rel_path = str(f.relative_to(project_path))

        # Multi-agent detection
        for pattern in MULTI_AGENT_PATTERNS:
            if re.search(pattern, content):
                has_multi_agent = True
                break

        # Escalation detection
        for pattern in ESCALATION_PATTERNS:
            if re.search(pattern, content):
                has_escalation = True
                break

        # Silent error handlers
        for pattern, desc in SILENT_ERROR_PATTERNS:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                silent_error_hits.append((rel_path, line_num, desc))

        # Output validation
        for pattern in VALIDATION_PATTERNS:
            if re.search(pattern, content):
                has_output_validation = True
                break

        # Audit trail fields
        for pattern in AUDIT_TRAIL_PATTERNS:
            if re.search(pattern, content):
                audit_trail_count += 1
                break  # count per-file, not per-pattern

    # --- Score and report ---

    # 1. No owner/responsible_party in configs
    if not has_owner_field:
        score -= 3
        findings.append({
            "severity": "critical",
            "category": "art22_accountability",
            "title": "No accountability owner in configuration",
            "detail": (
                "No owner, responsible_party, or contact field found in any "
                "configuration file. There is no documented accountability owner "
                "for agent decisions."
            ),
            "fix": "Add an owner or responsible_party field to your agent/tool "
                   "configuration specifying who is accountable for the system's decisions.",
            "articles": ["EU AI Act Art. 22", "GDPR Art. 5(2)"],
        })
    else:
        findings.append({
            "severity": "pass",
            "category": "art22_accountability",
            "title": "Accountability owner declared in configuration",
            "detail": "Found owner or responsible_party field in configuration.",
        })

    # 2. Multi-agent without escalation
    if has_multi_agent and not has_escalation:
        score -= 4
        findings.append({
            "severity": "critical",
            "category": "art22_accountability",
            "title": "Multi-agent orchestration without escalation path",
            "detail": (
                "Multi-agent or tool-chaining patterns detected but no escalation "
                "handler or fallback to human found. If an agent in the chain fails "
                "or produces uncertain output, there is no defined path to resolution."
            ),
            "fix": "Add an escalation handler or human fallback for agent chains. "
                   "Define what happens when an agent in the pipeline fails or is uncertain.",
            "articles": ["EU AI Act Art. 22", "GDPR Art. 5(2)"],
        })
    elif has_multi_agent and has_escalation:
        findings.append({
            "severity": "pass",
            "category": "art22_accountability",
            "title": "Multi-agent orchestration has escalation path",
            "detail": "Agent orchestration found with escalation or fallback handler.",
        })

    # 3. Silent error handlers
    if silent_error_hits:
        score -= 3
        locations = [f"{h[0]}:{h[1]}" for h in silent_error_hits[:5]]
        descs = list({h[2] for h in silent_error_hits})
        findings.append({
            "severity": "critical",
            "category": "art22_accountability",
            "title": "Silent error handling on agent decision paths",
            "detail": (
                f"Found {len(silent_error_hits)} silent error handler(s) "
                f"({', '.join(descs)}). Errors are swallowed without human "
                f"notification. Locations: {', '.join(locations)}"
            ),
            "fix": "Replace silent error handlers with proper logging at warning/error "
                   "level and add human notification for failures on agent decision paths.",
            "articles": ["EU AI Act Art. 22", "GDPR Art. 5(2)"],
        })

    # 4. No output validation
    if not has_output_validation:
        score -= 3
        findings.append({
            "severity": "critical",
            "category": "art22_accountability",
            "title": "No output validation detected",
            "detail": (
                "No schema validation, type checking, or bounds checking found for "
                "agent outputs. Unvalidated output going to external systems creates "
                "unaccountable behavior."
            ),
            "fix": "Add output validation (Pydantic, JSON Schema, or manual type/bounds "
                   "checks) before agent output reaches external systems.",
            "articles": ["EU AI Act Art. 22"],
        })
    else:
        findings.append({
            "severity": "pass",
            "category": "art22_accountability",
            "title": "Output validation detected",
            "detail": "Found schema validation, type checking, or sanitization patterns.",
        })

    # 5. No audit trail
    if audit_trail_count == 0:
        score -= 2
        findings.append({
            "severity": "warning",
            "category": "art22_accountability",
            "title": "No audit trail for agent actions",
            "detail": (
                "No audit logging with timestamp, agent_id, input/output hash, "
                "or decision rationale found. Without an audit trail, accountability "
                "cannot be demonstrated."
            ),
            "fix": "Log agent actions with: timestamp, agent_id, input_hash, "
                   "output_hash, and decision_rationale.",
            "articles": ["EU AI Act Art. 22", "GDPR Art. 5(2)"],
        })
    else:
        findings.append({
            "severity": "pass",
            "category": "art22_accountability",
            "title": "Audit trail patterns detected",
            "detail": f"Found audit-related fields in {audit_trail_count} file(s).",
        })

    return {
        "name": "Art. 22 Accountability",
        "icon": "\U0001f4cb",
        "score": max(0, score),
        "max_score": 15,
        "findings": findings,
    }
