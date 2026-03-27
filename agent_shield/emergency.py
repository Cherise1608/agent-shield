"""Emergency mode — checks whether governance prerequisites are intact.

When escalation channels are unreachable, agents are operating without
human oversight. This violates EU AI Act Art. 14 (human oversight) and
Art. 9 (risk management). Emergency mode detects this and recommends
or enforces fail-closed.

Designed for the scenario: "Primary platform is down. What are the
agents doing?"
"""

from __future__ import annotations

import socket
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_governance(path: Path) -> dict[str, Any]:
    """Minimal YAML parser for governance.yaml — no PyYAML dependency."""
    result: dict[str, Any] = {}
    if not path.exists():
        return result

    lines = path.read_text().splitlines()
    current_section = ""
    current_subsection = ""
    current_list_key = ""
    current_list_item: dict[str, str] = {}

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level key
        if not stripped.startswith(" "):
            current_section = stripped.rstrip(":")
            result[current_section] = {}
            current_subsection = ""
            current_list_key = ""
            continue

        indent = len(line) - len(line.lstrip())

        # Second-level key or list
        if indent == 2:
            if ":" in stripped and not stripped.strip().startswith("-"):
                key, _, val = stripped.strip().partition(":")
                key = key.strip()
                val = val.strip()
                if val:
                    result[current_section][key] = val
                else:
                    current_list_key = key
                    result[current_section][key] = []
                current_subsection = key
            elif stripped.strip().startswith("-"):
                # Simple list item at indent 2
                val = stripped.strip().lstrip("- ").strip()
                if current_list_key and isinstance(result[current_section].get(current_list_key), list):
                    result[current_section][current_list_key].append(val)
            continue

        # Third-level: list items with sub-keys
        if indent >= 4:
            if stripped.strip().startswith("- "):
                # Start of a new list item
                if current_list_item and current_list_key:
                    result[current_section][current_list_key].append(current_list_item)
                current_list_item = {}
                rest = stripped.strip()[2:]
                if ":" in rest:
                    k, _, v = rest.partition(":")
                    current_list_item[k.strip()] = v.strip()
            elif ":" in stripped and current_list_item is not None:
                k, _, v = stripped.strip().partition(":")
                current_list_item[k.strip()] = v.strip()

    # Flush last list item
    if current_list_item and current_list_key and current_section in result:
        if isinstance(result[current_section].get(current_list_key), list):
            result[current_section][current_list_key].append(current_list_item)

    return result


# ── Channel health checks ──────────────────────────────────────────


def _check_http(url: str, timeout: int = 5) -> tuple[bool, str]:
    """Check if an HTTP(S) endpoint responds."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return True, f"HTTP {resp.status}"
    except urllib.error.URLError as e:
        return False, f"Unreachable: {e.reason}"
    except Exception as e:
        return False, f"Error: {e}"


def _check_tcp(host: str, port: int, timeout: int = 5) -> tuple[bool, str]:
    """Check if a TCP port is open."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True, f"TCP {host}:{port} open"
    except OSError as e:
        return False, f"TCP {host}:{port} closed: {e}"


def _check_process(name: str) -> tuple[bool, str]:
    """Check if a process is running (by name substring)."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", name],
            capture_output=True, timeout=5,
        )
        if result.returncode == 0:
            pids = result.stdout.decode().strip().split("\n")
            return True, f"Process '{name}' running (PID: {pids[0]})"
        return False, f"Process '{name}' not found"
    except FileNotFoundError:
        return False, "pgrep not available"
    except Exception as e:
        return False, f"Error: {e}"


def _check_file(path: str) -> tuple[bool, str]:
    """Check if a file/socket/pipe exists and is writable."""
    p = Path(path)
    if p.exists():
        if p.is_socket() or p.is_fifo():
            return True, f"Socket/pipe exists: {path}"
        if p.is_file():
            try:
                with open(p, "a"):
                    pass
                return True, f"File writable: {path}"
            except OSError:
                return False, f"File not writable: {path}"
    return False, f"Path not found: {path}"


def check_channel(channel: dict[str, str]) -> dict[str, Any]:
    """Check a single escalation channel's health.

    Supported channel types (detected from endpoint field):
    - http:// or https:// → HTTP HEAD check
    - tcp://host:port → TCP socket check
    - process://name → pgrep check
    - file:///path → file/socket existence check
    - (no endpoint) → assumed unavailable
    """
    name = channel.get("channel", "unknown")
    endpoint = channel.get("endpoint", "")
    trigger = channel.get("trigger", "unknown")

    result: dict[str, Any] = {
        "channel": name,
        "trigger": trigger,
        "endpoint": endpoint or "(not configured)",
        "reachable": False,
        "detail": "",
    }

    if not endpoint:
        # No endpoint configured — channel is uncheckable
        # If it's a built-in action like "abort", it's always available
        if name == "abort":
            result["reachable"] = True
            result["detail"] = "Built-in action, always available"
        else:
            result["reachable"] = False
            result["detail"] = "No endpoint configured — cannot verify reachability"
        return result

    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        ok, detail = _check_http(endpoint)
    elif endpoint.startswith("tcp://"):
        parts = endpoint[6:].split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 443
        ok, detail = _check_tcp(host, port)
    elif endpoint.startswith("process://"):
        ok, detail = _check_process(endpoint[10:])
    elif endpoint.startswith("file://"):
        ok, detail = _check_file(endpoint[7:])
    else:
        ok, detail = False, f"Unknown endpoint scheme: {endpoint}"

    result["reachable"] = ok
    result["detail"] = detail
    return result


# ── Emergency assessment ────────────────────────────────────────────


def assess_emergency(governance_path: Path) -> dict[str, Any]:
    """Run full emergency assessment against a governance.yaml.

    Returns a structured result with:
    - channel checks
    - governance status
    - human oversight availability
    - recommended action
    - regulatory impact
    """
    assessment: dict[str, Any] = {
        "timestamp": _iso_now(),
        "governance_file": str(governance_path),
        "channels": [],
        "governance_intact": False,
        "human_oversight_available": False,
        "fail_mode": "unknown",
        "recommended_action": "",
        "regulatory_impact": {},
    }

    gov = _parse_governance(governance_path)

    if not gov:
        assessment["recommended_action"] = "HALT — no governance.yaml found"
        assessment["regulatory_impact"] = {
            "eu_ai_act_art_9": "VIOLATION — no risk management system",
            "eu_ai_act_art_14": "VIOLATION — no human oversight mechanism",
        }
        return assessment

    # Get fail_mode
    runtime = gov.get("runtime", {})
    fail_mode = runtime.get("fail_mode", "closed")
    assessment["fail_mode"] = fail_mode

    # Get escalation channels
    delegation = gov.get("delegation", {})
    channels = delegation.get("escalation", [])

    if not channels:
        assessment["recommended_action"] = "HALT — no escalation channels defined"
        assessment["regulatory_impact"] = {
            "eu_ai_act_art_14": "VIOLATION — no escalation path to human reviewer",
        }
        return assessment

    # Check each channel
    human_channels_reachable = 0
    human_channels_total = 0

    for ch in channels:
        if not isinstance(ch, dict):
            continue
        check = check_channel(ch)
        assessment["channels"].append(check)

        # Count human-facing channels (everything except "abort")
        if ch.get("channel") != "abort":
            human_channels_total += 1
            if check["reachable"]:
                human_channels_reachable += 1

    # Determine status
    if human_channels_total == 0:
        assessment["human_oversight_available"] = False
        assessment["governance_intact"] = False
        assessment["recommended_action"] = "HALT — no human oversight channels defined"
    elif human_channels_reachable == 0:
        assessment["human_oversight_available"] = False
        assessment["governance_intact"] = False
        assessment["recommended_action"] = (
            "EMERGENCY — all human oversight channels unreachable. "
            "Switch to fail-closed. Halt all autonomous agents until "
            "communication is restored."
        )
    elif human_channels_reachable < human_channels_total:
        assessment["human_oversight_available"] = True
        assessment["governance_intact"] = False
        assessment["recommended_action"] = (
            f"DEGRADED — {human_channels_reachable}/{human_channels_total} "
            f"oversight channels reachable. Monitor closely. "
            f"Reduce max_autonomous_actions."
        )
    else:
        assessment["human_oversight_available"] = True
        assessment["governance_intact"] = True
        assessment["recommended_action"] = "NOMINAL — all oversight channels operational"

    # Regulatory impact
    assessment["regulatory_impact"] = {
        "eu_ai_act_art_9": (
            "COMPLIANT" if assessment["governance_intact"]
            else "AT RISK — governance prerequisites degraded"
        ),
        "eu_ai_act_art_14": (
            "COMPLIANT" if assessment["human_oversight_available"]
            else "VIOLATION — human oversight unreachable"
        ),
    }

    return assessment


def format_emergency_text(result: dict[str, Any]) -> str:
    """Format emergency assessment as human-readable text."""
    lines = [
        "agent-shield status --emergency",
        "=" * 56,
        f"  Timestamp:    {result['timestamp']}",
        f"  Governance:   {result['governance_file']}",
        f"  Fail mode:    {result['fail_mode']}",
        "",
        "  Escalation Channels",
        "  " + "-" * 40,
    ]

    for ch in result.get("channels", []):
        status = "UP" if ch["reachable"] else "DOWN"
        icon = "[+]" if ch["reachable"] else "[X]"
        lines.append(f"  {icon} {ch['channel']:<20} {status}")
        lines.append(f"      endpoint: {ch['endpoint']}")
        lines.append(f"      detail:   {ch['detail']}")

    if not result.get("channels"):
        lines.append("  (no channels configured)")

    lines.append("")
    lines.append("  Assessment")
    lines.append("  " + "-" * 40)

    oversight = "YES" if result["human_oversight_available"] else "NO"
    intact = "YES" if result["governance_intact"] else "NO"
    lines.append(f"  Human oversight available:  {oversight}")
    lines.append(f"  Governance intact:          {intact}")
    lines.append(f"  Action: {result['recommended_action']}")

    lines.append("")
    lines.append("  Regulatory Impact")
    lines.append("  " + "-" * 40)
    for reg, status in result.get("regulatory_impact", {}).items():
        label = reg.replace("_", " ").replace("eu ai act ", "EU AI Act ").replace("art ", "Art. ")
        lines.append(f"  {label}: {status}")

    lines.append("=" * 56)
    return "\n".join(lines)
