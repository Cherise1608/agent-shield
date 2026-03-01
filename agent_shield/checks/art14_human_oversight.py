"""Check for automated decision paths without human review (EU AI Act Article 14)."""
import re
from pathlib import Path

# LLM/agent output used directly in conditionals
LLM_CONDITIONAL_PATTERNS = [
    (r'if\s+(?:llm|gpt|claude|agent|model|ai)[_\.]?(?:response|output|result|answer|decision)\s*[=!<>]', "LLM output in conditional"),
    (r'if\s+(?:response|result|output)\s*==\s*["\'](?:approve|yes|true|allow|accept)', "LLM string match driving decision"),
    (r'if\s+(?:agent|bot|assistant)\.(?:decide|judge|evaluate|classify|determine)\s*\(', "Agent decision method in conditional"),
    (r'(?:response|result|output|decision)\s*=\s*(?:llm|gpt|claude|agent|model)\..+\n\s*if\s+(?:response|result|output|decision)', "LLM call immediately followed by conditional"),
]

# Auto-* function patterns (risk: automation without human checkpoint)
AUTO_FUNCTION_PATTERNS = [
    r'(?i)def\s+auto[_\-]?approve',
    r'(?i)def\s+auto[_\-]?decide',
    r'(?i)def\s+auto[_\-]?execute',
    r'(?i)def\s+auto[_\-]?process',
    r'(?i)def\s+auto[_\-]?classify',
    r'(?i)def\s+auto[_\-]?route',
    r'(?i)def\s+auto[_\-]?assign',
]

# Human review companion patterns (presence = mitigating factor)
HUMAN_REVIEW_PATTERNS = [
    r'(?i)human[_\-]?review',
    r'(?i)human[_\-]?approval',
    r'(?i)human[_\-]?oversight',
    r'(?i)human[_\-]?intervention',
    r'(?i)manual[_\-]?review',
    r'(?i)require[_\-]?approval',
    r'(?i)pending[_\-]?review',
    r'(?i)approval[_\-]?gate',
]

# Agent output piped directly to system actions
DIRECT_ACTION_PATTERNS = [
    (r'(?:llm|agent|model|gpt|claude|ai)[_\.]?(?:response|output|result).{0,80}(?:\.execute|\.run|\.send|\.write|\.delete|\.update|\.insert|\.post|\.put|\.patch)', "Agent output piped to system action"),
    (r'(?:cursor|db|conn|session|collection)\.(?:execute|insert|update|delete|write)\(.{0,40}(?:response|output|result|answer)', "Agent output in database operation"),
    (r'(?:requests|httpx|aiohttp|fetch|axios)\.\w+\(.{0,60}(?:response|output|result)', "Agent output in HTTP request"),
    (r'(?:send_email|send_message|send_notification|publish)\(.{0,60}(?:response|output|result)', "Agent output in outbound communication"),
    (r'(?:open|write_text|write_bytes)\(.{0,60}(?:response|output|result)', "Agent output written to file"),
    (r'(?:subprocess|os\.system|exec|eval)\(.{0,60}(?:response|output|result)', "Agent output in code execution"),
]


def check_art14_human_oversight(project_path: Path, files: list[Path]) -> dict:
    """Check for automated decision paths without human review. Max 15 points."""
    score = 15
    findings = []
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}

    llm_conditional_hits = []
    auto_func_hits = []
    direct_action_hits = []
    has_human_review = False

    for f in files:
        if f.suffix not in code_extensions:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        rel_path = str(f.relative_to(project_path))

        # Check for human review patterns (mitigating factor)
        for pattern in HUMAN_REVIEW_PATTERNS:
            if re.search(pattern, content):
                has_human_review = True
                break

        # Check LLM output in conditionals
        for pattern, desc in LLM_CONDITIONAL_PATTERNS:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                llm_conditional_hits.append((rel_path, line_num, desc))

        # Check auto-* functions
        for pattern in AUTO_FUNCTION_PATTERNS:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                func_name = match.group().split("def ")[-1].strip()
                auto_func_hits.append((rel_path, line_num, func_name))

        # Check direct action patterns
        for pattern, desc in DIRECT_ACTION_PATTERNS:
            for match in re.finditer(pattern, content, re.DOTALL):
                line_num = content[:match.start()].count("\n") + 1
                direct_action_hits.append((rel_path, line_num, desc))

    # --- Score and report ---

    if llm_conditional_hits:
        score -= 5
        locations = [f"{h[0]}:{h[1]}" for h in llm_conditional_hits[:5]]
        findings.append({
            "severity": "critical",
            "category": "art14_human_oversight",
            "title": "LLM output used directly in decision conditional",
            "detail": (
                f"Found {len(llm_conditional_hits)} instance(s) where LLM/agent output "
                f"drives a decision without human validation: {', '.join(locations)}"
            ),
            "fix": "Add a human review step between LLM output and decision execution. "
                   "Route uncertain or high-impact decisions to a human reviewer.",
            "articles": ["EU AI Act Art. 14"],
        })

    if auto_func_hits and not has_human_review:
        score -= 4
        locations = [f"{h[0]}:{h[1]} ({h[2]})" for h in auto_func_hits[:5]]
        findings.append({
            "severity": "critical",
            "category": "art14_human_oversight",
            "title": "Automated decision function without human review companion",
            "detail": (
                f"Found auto-* functions with no corresponding human review mechanism: "
                f"{', '.join(locations)}"
            ),
            "fix": "Add a human_review or approval_gate function that can intercept "
                   "or override automated decisions.",
            "articles": ["EU AI Act Art. 14"],
        })
    elif auto_func_hits and has_human_review:
        findings.append({
            "severity": "pass",
            "category": "art14_human_oversight",
            "title": "Automated functions have human review companion",
            "detail": "Auto-* functions found alongside human review mechanisms.",
        })

    if direct_action_hits:
        score -= 5
        locations = [f"{h[0]}:{h[1]}" for h in direct_action_hits[:5]]
        descs = list({h[2] for h in direct_action_hits})
        findings.append({
            "severity": "critical",
            "category": "art14_human_oversight",
            "title": "Agent output flows directly to system action",
            "detail": (
                f"Found {len(direct_action_hits)} instance(s) where agent output "
                f"reaches a system action without human checkpoint: "
                f"{', '.join(descs[:3])}. Locations: {', '.join(locations)}"
            ),
            "fix": "Insert an approval step or validation layer between agent output "
                   "and system actions. EU AI Act Article 14 requires humans can "
                   "intervene or interrupt the system for high-risk AI.",
            "articles": ["EU AI Act Art. 14"],
        })

    if not llm_conditional_hits and not auto_func_hits and not direct_action_hits:
        findings.append({
            "severity": "pass",
            "category": "art14_human_oversight",
            "title": "No unreviewed automated decision paths detected",
            "detail": "No patterns found where agent output drives actions without a human checkpoint.",
        })

    return {
        "name": "Art. 14 Human Oversight",
        "icon": "\u2696\ufe0f",
        "score": max(0, score),
        "max_score": 15,
        "findings": findings,
    }
