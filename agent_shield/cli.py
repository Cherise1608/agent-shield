"""Command-line interface for agent-shield."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

from agent_shield import __version__
from agent_shield.scanner import scan_project
from agent_shield.frameworks import FRAMEWORKS, get_framework
from agent_shield.formatters import format_results


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

    return parser


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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
