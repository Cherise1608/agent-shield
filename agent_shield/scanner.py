"""Core scanning logic — orchestrates check modules and computes scores."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_shield.checks.secrets import check_secrets
from agent_shield.checks.audit_logging import check_audit_logging
from agent_shield.checks.human_oversight import check_human_oversight
from agent_shield.checks.data_classification import check_data_classification
from agent_shield.checks.error_handling import check_error_handling
from agent_shield.checks.documentation import check_documentation
from agent_shield.frameworks import Framework


# Registry: (check_function, function_name_for_framework_filtering)
ALL_CHECKS = [
    (check_secrets, "check_secrets"),
    (check_audit_logging, "check_audit_logging"),
    (check_human_oversight, "check_human_oversight"),
    (check_data_classification, "check_data_classification"),
    (check_error_handling, "check_error_handling"),
    (check_documentation, "check_documentation"),
]


def _collect_files(project_path: Path) -> list[Path]:
    """Collect all non-hidden files in the project tree."""
    files: list[Path] = []
    for item in project_path.rglob("*"):
        if item.is_file() and not any(p.startswith(".") for p in item.relative_to(project_path).parts):
            files.append(item)
    return files


def scan_project(project_path: Path, framework: Framework) -> dict[str, Any]:
    """Run all applicable checks and return a structured results dict."""
    files = _collect_files(project_path)

    check_results: list[dict[str, Any]] = []
    for check_fn, check_name in ALL_CHECKS:
        # Skip checks not relevant to the selected framework
        if framework.name != "all" and check_name not in framework.checks:
            continue
        result = check_fn(project_path, files)
        check_results.append(result)

    total_score = sum(r["score"] for r in check_results)
    total_max = sum(r["max_score"] for r in check_results)
    pct = round((total_score / total_max) * 100) if total_max > 0 else 0

    # Count severities across all findings
    all_findings = [f for r in check_results for f in r.get("findings", [])]
    critical = sum(1 for f in all_findings if f["severity"] == "critical")
    warnings = sum(1 for f in all_findings if f["severity"] == "warning")
    passed = sum(1 for f in all_findings if f["severity"] == "pass")

    return {
        "project": str(project_path),
        "framework": framework.name,
        "score": total_score,
        "max_score": total_max,
        "pct": pct,
        "summary": {"passed": passed, "warnings": warnings, "critical": critical},
        "checks": check_results,
    }
