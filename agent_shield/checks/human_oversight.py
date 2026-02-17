"""Check for human oversight and control mechanisms."""
import re
from pathlib import Path

HITL_PATTERNS = [
    (r'(?i)human[_\-]?(in[_\-]?the[_\-]?loop|review|approval|confirm)', "Human-in-the-loop", 5),
    (r'(?i)require[_\-]?approval|needs[_\-]?approval|pending[_\-]?approval', "Approval gate", 5),
    (r'(?i)manual[_\-]?review|manual[_\-]?check', "Manual review step", 4),
    (r'(?i)confirm.*before|approve.*before|review.*before', "Pre-action confirmation", 4),
]

ESCALATION_PATTERNS = [
    (r'(?i)escalat(e|ion)|elevat(e|ion)', "Escalation logic", 4),
    (r'(?i)fallback[_\-]?to[_\-]?human|hand[_\-]?off|handoff', "Human handoff", 4),
    (r'(?i)confidence[_\-]?(score|threshold|level).*(?:low|below|under)', "Confidence-based escalation", 4),
    (r'(?i)risk[_\-]?(score|level|threshold)', "Risk-based routing", 3),
]

OVERRIDE_PATTERNS = [
    (r'(?i)kill[_\-]?switch|emergency[_\-]?stop|abort', "Kill switch", 4),
    (r'(?i)override|force[_\-]?stop|disable[_\-]?agent', "Override mechanism", 3),
    (r'(?i)rate[_\-]?limit|throttle|circuit[_\-]?break', "Rate limiting / circuit breaker", 3),
    (r'(?i)max[_\-]?(retries|attempts|iterations|loops)', "Loop bounds", 2),
]

EXTERNAL_ACTION_PATTERNS = [
    (r'(?i)(send|post|publish|deploy|delete|drop|execute).*confirm', "Confirmation before destructive action", 4),
    (r'(?i)dry[_\-]?run|sandbox|preview', "Dry run / sandbox mode", 3),
    (r'(?i)allow[_\-]?list|whitelist|permitted[_\-]?actions', "Action allowlisting", 3),
]

def check_human_oversight(project_path: Path, files: list[Path]) -> dict:
    """Check for human oversight mechanisms. Max 20 points."""
    score = 0
    findings = []
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".yaml", ".yml"}

    has_hitl = False
    has_escalation = False
    has_override = False
    has_external_gates = False

    for f in files:
        if f.suffix not in code_extensions:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        for pattern, name, points in HITL_PATTERNS:
            if re.search(pattern, content):
                has_hitl = True

        for pattern, name, points in ESCALATION_PATTERNS:
            if re.search(pattern, content):
                has_escalation = True

        for pattern, name, points in OVERRIDE_PATTERNS:
            if re.search(pattern, content):
                has_override = True

        for pattern, name, points in EXTERNAL_ACTION_PATTERNS:
            if re.search(pattern, content):
                has_external_gates = True

    if has_hitl:
        score += 7
        findings.append({
            "severity": "pass",
            "category": "human_oversight",
            "title": "Human-in-the-loop pattern detected",
            "detail": "Found approval gate or human review requirement.",
        })
    else:
        findings.append({
            "severity": "critical",
            "category": "human_oversight",
            "title": "No human-in-the-loop pattern detected",
            "detail": "No human approval, review, or confirmation gate found in agent logic.",
            "fix": "Add a human approval gate before high-risk agent actions (external API calls, data writes, user-facing communications).",
            "articles": ["EU AI Act Art. 14"],
        })

    if has_escalation:
        score += 5
        findings.append({
            "severity": "pass",
            "category": "human_oversight",
            "title": "Escalation logic detected",
            "detail": "Found confidence-based escalation, human handoff, or risk routing.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "human_oversight",
            "title": "No escalation logic detected",
            "detail": "No pattern for escalating uncertain or high-risk decisions to humans.",
            "fix": "Add escalation logic: if confidence < threshold or risk > threshold, route to human.",
            "articles": ["EU AI Act Art. 14"],
        })

    if has_override:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "human_oversight",
            "title": "Override / kill switch detected",
            "detail": "Found emergency stop, rate limiting, or loop bounds.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "human_oversight",
            "title": "No override mechanism detected",
            "detail": "No kill switch, circuit breaker, or emergency stop pattern found.",
            "fix": "Add a kill switch or circuit breaker that halts agent execution on anomalous behavior.",
            "articles": ["EU AI Act Art. 14"],
        })

    if has_external_gates:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "human_oversight",
            "title": "External action gates detected",
            "detail": "Found confirmation gates, dry-run modes, or action allowlisting.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "human_oversight",
            "title": "No external action gates detected",
            "detail": "No confirmation step before destructive or external actions.",
            "fix": "Add confirmation or dry-run mode for actions that affect external systems.",
            "articles": ["EU AI Act Art. 14", "GDPR Art. 22"],
        })

    return {
        "name": "Human Oversight",
        "icon": "👤",
        "score": min(score, 20),
        "max_score": 20,
        "findings": findings,
    }
