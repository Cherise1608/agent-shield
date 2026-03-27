"""Command-line interface for agent-shield."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

from agent_shield import __version__
from agent_shield.scanner import scan_project
from agent_shield.frameworks import FRAMEWORKS, get_framework
from agent_shield.formatters import format_results
from agent_shield.report import (
    query_entries,
    summarize,
    compliance_summary,
    verify_chain,
    DEFAULT_REPORT_PATH,
)


def _parse_duration(value: str) -> float:
    """Parse a duration string like '24h', '7d', '30m' into hours."""
    value = value.strip().lower()
    if value.endswith("d"):
        return float(value[:-1]) * 24
    if value.endswith("h"):
        return float(value[:-1])
    if value.endswith("m"):
        return float(value[:-1]) / 60
    return float(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-shield",
        description="Governance readiness scanner for AI agent projects.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"agent-shield {__version__}",
    )

    sub = parser.add_subparsers(dest="command")

    # --- scan command ---
    scan_parser = sub.add_parser(
        "scan",
        help="Scan a project directory for governance readiness.",
    )
    scan_parser.add_argument(
        "path",
        type=str,
        default=".",
        nargs="?",
        help="Path to the project root (default: current directory).",
    )
    scan_parser.add_argument(
        "--framework",
        type=str,
        choices=list(FRAMEWORKS.keys()),
        default="all",
        help="Governance framework to check against (default: all).",
    )
    scan_parser.add_argument(
        "--format",
        dest="output_format",
        type=str,
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )

    # --- report command ---
    report_parser = sub.add_parser(
        "report",
        help="Show governance report summary from the audit ledger.",
    )
    report_parser.add_argument(
        "--last",
        type=str,
        default=None,
        metavar="DURATION",
        help="Filter to last N hours/days (e.g. '24h', '7d', '30m').",
    )
    report_parser.add_argument(
        "--ledger",
        type=str,
        default=str(DEFAULT_REPORT_PATH),
        help=f"Path to governance-report.json (default: {DEFAULT_REPORT_PATH}).",
    )
    report_parser.add_argument(
        "--format",
        dest="output_format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )

    # --- compliance command ---
    compliance_parser = sub.add_parser(
        "compliance",
        help="Show compliance status for a regulatory framework.",
    )
    compliance_parser.add_argument(
        "--framework",
        type=str,
        required=True,
        choices=["eu-ai-act", "gdpr"],
        help="Regulatory framework to evaluate against.",
    )
    compliance_parser.add_argument(
        "--last",
        type=str,
        default=None,
        metavar="DURATION",
        help="Filter to last N hours/days (e.g. '24h', '7d').",
    )
    compliance_parser.add_argument(
        "--ledger",
        type=str,
        default=str(DEFAULT_REPORT_PATH),
        help=f"Path to governance-report.json (default: {DEFAULT_REPORT_PATH}).",
    )
    compliance_parser.add_argument(
        "--format",
        dest="output_format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )

    # --- verify command ---
    verify_parser = sub.add_parser(
        "verify",
        help="Verify hash chain integrity of the audit ledger.",
    )
    verify_parser.add_argument(
        "--ledger",
        type=str,
        default=str(DEFAULT_REPORT_PATH),
        help=f"Path to governance-report.json (default: {DEFAULT_REPORT_PATH}).",
    )

    return parser


def _format_report_text(summary: dict) -> str:
    status = summary["governance_status"]
    status_line = {
        "ENFORCED": "ENFORCED — governance active and blocking violations",
        "DEGRADED": "DEGRADED — drift detected without escalation",
        "UNMONITORED": "UNMONITORED — no governance entries found",
    }.get(status, status)

    lines = [
        "agent-shield report",
        "=" * 52,
        f"  Total actions evaluated:   {summary['total_actions']}",
        f"  Actions blocked:           {summary['actions_blocked']}",
        f"  Actions allowed:           {summary['actions_allowed']}",
        f"  Drift events (>0.3):       {summary['drift_events']}",
        f"  Escalations triggered:     {summary['escalations_triggered']}",
        "=" * 52,
        f"  Governance status:         {status_line}",
    ]
    return "\n".join(lines)


def _format_compliance_text(result: dict) -> str:
    fw = result.get("framework", "Unknown")
    lines = [
        f"agent-shield compliance  |  {fw}",
        "=" * 52,
        f"  Entries evaluated: {result.get('entries_evaluated', 0)}",
    ]

    if result.get("error"):
        lines.append(f"  Error: {result['error']}")
        return "\n".join(lines)

    if "article_12_coverage" in result:
        lines.append(f"  Art. 12 coverage:    {result['article_12_coverage']} ({result['article_12_detail']})")
        lines.append(f"  Art. 14 compliant:   {'Yes' if result['article_14_compliant'] else 'NO'} ({result['article_14_detail']})")
    if "article_22_flags" in result:
        lines.append(f"  Art. 22 flags:       {result['article_22_flags']} ({result['article_22_detail']})")
        lines.append(f"  Art. 35 flags:       {result['article_35_flags']} ({result['article_35_detail']})")

    lines.append("=" * 52)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "scan":
        project_path = Path(args.path).resolve()
        if not project_path.is_dir():
            print(f"Error: '{project_path}' is not a directory.", file=sys.stderr)
            return 1

        framework = get_framework(args.framework)
        logger.info("Scanning %s with framework '%s'", project_path, framework.name)
        results = scan_project(project_path, framework)
        output = format_results(results, args.output_format)
        print(output)

        # Exit code: 0 if percentage >= 70, 1 otherwise (useful for CI gates)
        return 0 if results["pct"] >= 70 else 1

    if args.command == "report":
        ledger = Path(args.ledger)
        last_hours = _parse_duration(args.last) if args.last else None
        entries = query_entries(path=ledger, last_hours=last_hours)
        summary = summarize(entries)

        if args.output_format == "json":
            print(json.dumps(summary, indent=2))
        else:
            print(_format_report_text(summary))
        return 0

    if args.command == "compliance":
        ledger = Path(args.ledger)
        last_hours = _parse_duration(args.last) if args.last else None
        entries = query_entries(path=ledger, last_hours=last_hours)
        result = compliance_summary(entries, args.framework)

        if args.output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(_format_compliance_text(result))
        return 0

    if args.command == "verify":
        ledger = Path(args.ledger)
        valid, count, message = verify_chain(path=ledger)
        print(f"Chain verification: {'PASS' if valid else 'FAIL'}")
        print(f"  {message}")
        return 0 if valid else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
