"""Output formatters: text, json, markdown."""

from __future__ import annotations

import json
from typing import Any

SEVERITY_ICON_TEXT = {"pass": "[PASS]", "warning": "[WARN]", "critical": "[CRIT]"}
SEVERITY_ICON_MD = {"pass": "\u2705", "warning": "\u26a0\ufe0f", "critical": "\u274c"}


def format_results(results: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return _format_json(results)
    if fmt == "markdown":
        return _format_markdown(results)
    return _format_text(results)


def _format_text(results: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"agent-shield scan  |  framework: {results['framework']}")
    lines.append(f"Project: {results['project']}")
    lines.append("=" * 64)

    for check in results["checks"]:
        lines.append(f"\n  {check.get('icon', '#')} {check['name']}  ({check['score']}/{check['max_score']})")
        for finding in check.get("findings", []):
            icon = SEVERITY_ICON_TEXT.get(finding["severity"], "[???]")
            lines.append(f"    {icon} {finding['title']}")
            lines.append(f"           {finding['detail']}")
            if "fix" in finding:
                lines.append(f"           Fix: {finding['fix']}")
            if "articles" in finding and finding["articles"]:
                lines.append(f"           Ref: {', '.join(finding['articles'])}")

    lines.append("\n" + "=" * 64)
    s = results["summary"]
    lines.append(
        f"Score: {results['score']}/{results['max_score']} ({results['pct']}%)  "
        f"|  passed: {s['passed']}  warnings: {s['warnings']}  critical: {s['critical']}"
    )
    return "\n".join(lines)


def _format_json(results: dict[str, Any]) -> str:
    return json.dumps(results, indent=2, default=str)


def _format_markdown(results: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# agent-shield scan")
    lines.append(f"**Framework:** {results['framework']}  ")
    lines.append(f"**Project:** `{results['project']}`  ")
    lines.append(f"**Score:** {results['score']}/{results['max_score']} ({results['pct']}%)\n")

    for check in results["checks"]:
        lines.append(f"## {check.get('icon', '#')} {check['name']}  ({check['score']}/{check['max_score']})\n")
        lines.append("| Status | Finding | Detail |")
        lines.append("|--------|---------|--------|")
        for finding in check.get("findings", []):
            icon = SEVERITY_ICON_MD.get(finding["severity"], "\u2753")
            detail = finding["detail"]
            if "fix" in finding:
                detail += f" **Fix:** {finding['fix']}"
            lines.append(f"| {icon} | {finding['title']} | {detail} |")
        lines.append("")

    s = results["summary"]
    lines.append(
        f"---\n**Total: {results['score']}/{results['max_score']} ({results['pct']}%)** — "
        f"passed: {s['passed']}, warnings: {s['warnings']}, critical: {s['critical']}"
    )
    return "\n".join(lines)
