"""Governance reporting — append-only ledger with chain integrity."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_PATH = Path("governance-report.json")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _read_ledger(path: Path) -> list[dict[str, Any]]:
    """Read existing ledger entries. Returns empty list if file missing or corrupt."""
    if not path.exists():
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _last_hash(entries: list[dict[str, Any]]) -> str:
    """Return the hash of the last entry, or a genesis hash."""
    if not entries:
        return _sha256("genesis")
    last = entries[-1]
    return last.get("entry_hash", _sha256("genesis"))


def _compute_entry_hash(entry: dict[str, Any], previous_hash: str) -> str:
    """Chain hash: sha256(previous_hash + canonical JSON of entry)."""
    payload = previous_hash + json.dumps(entry, sort_keys=True, default=str)
    return _sha256(payload)


def create_entry(
    agent_name: str,
    action_attempted: str,
    policy_matched: str,
    result: str,
    exit_code: int,
    drift_score: float = 0.0,
    escalation: bool = False,
    pii_touched: bool = False,
    human_review_available: bool = True,
) -> dict[str, Any]:
    """Build a single ledger entry with compliance mapping."""
    # Compliance mapping derived from action context
    entry = {
        "timestamp": _iso_now(),
        "agent_name": agent_name,
        "action_attempted": action_attempted,
        "policy_matched": policy_matched,
        "result": result,
        "exit_code": exit_code,
        "drift_score": round(drift_score, 4),
        "escalation": escalation,
        "compliance_mapping": {
            # Art. 12: logging — true if this entry exists (it does)
            "eu_ai_act_article_12": True,
            # Art. 14: human oversight — true if escalation paths work
            "eu_ai_act_article_14": escalation or human_review_available,
            # Art. 22: automated decisions without human review
            "gdpr_article_22": result == "ALLOWED" and not escalation and not human_review_available,
            # Art. 35: DPIA-relevant if PII data is involved
            "gdpr_article_35": pii_touched,
        },
    }
    return entry


def append_entry(entry: dict[str, Any], path: Path = DEFAULT_REPORT_PATH) -> dict[str, Any]:
    """Append an entry to the ledger with chain integrity hash."""
    entries = _read_ledger(path)
    prev_hash = _last_hash(entries)

    entry["previous_hash"] = prev_hash
    entry["entry_hash"] = _compute_entry_hash(entry, prev_hash)

    entries.append(entry)

    with open(path, "w") as f:
        json.dump(entries, f, indent=2, default=str)

    return entry


def verify_chain(path: Path = DEFAULT_REPORT_PATH) -> tuple[bool, int, str]:
    """Verify the hash chain integrity. Returns (valid, entries_checked, message)."""
    entries = _read_ledger(path)
    if not entries:
        return True, 0, "Empty ledger."

    prev_hash = _sha256("genesis")
    for i, entry in enumerate(entries):
        stored_hash = entry.get("entry_hash", "")
        entry_copy = {k: v for k, v in entry.items() if k not in ("entry_hash", "previous_hash")}
        entry_copy["previous_hash"] = prev_hash
        expected = _compute_entry_hash(entry_copy, prev_hash)
        if stored_hash != expected:
            return False, i, f"Chain broken at entry {i}: expected {expected[:16]}..., got {stored_hash[:16]}..."
        prev_hash = stored_hash

    return True, len(entries), f"Chain intact. {len(entries)} entries verified."


def query_entries(
    path: Path = DEFAULT_REPORT_PATH,
    last_hours: float | None = None,
) -> list[dict[str, Any]]:
    """Return ledger entries, optionally filtered to the last N hours."""
    entries = _read_ledger(path)
    if last_hours is None:
        return entries

    cutoff = datetime.now(timezone.utc).timestamp() - (last_hours * 3600)
    filtered = []
    for e in entries:
        try:
            ts = datetime.fromisoformat(e["timestamp"]).timestamp()
            if ts >= cutoff:
                filtered.append(e)
        except (KeyError, ValueError):
            continue
    return filtered


def summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute summary statistics from a set of ledger entries."""
    total = len(entries)
    blocked = sum(1 for e in entries if e.get("result") == "BLOCKED")
    allowed = sum(1 for e in entries if e.get("result") == "ALLOWED")
    drift_events = sum(1 for e in entries if e.get("drift_score", 0) > 0.3)
    escalations = sum(1 for e in entries if e.get("escalation"))

    # Governance status
    if total == 0:
        status = "UNMONITORED"
    elif blocked > 0 or drift_events > 0:
        status = "ENFORCED"
    else:
        status = "ENFORCED"

    # Degrade if there are drift events without escalation
    unescalated_drift = sum(
        1 for e in entries
        if e.get("drift_score", 0) > 0.3 and not e.get("escalation")
    )
    if unescalated_drift > 0:
        status = "DEGRADED"

    return {
        "total_actions": total,
        "actions_blocked": blocked,
        "actions_allowed": allowed,
        "drift_events": drift_events,
        "escalations_triggered": escalations,
        "governance_status": status,
    }


def compliance_summary(entries: list[dict[str, Any]], framework: str) -> dict[str, Any]:
    """Compute compliance metrics for a given framework."""
    total = len(entries)
    if total == 0:
        return {"framework": framework, "entries_evaluated": 0, "message": "No entries to evaluate."}

    if framework == "eu-ai-act":
        # Art. 12: percentage with complete audit trail (entry_hash present)
        art12_count = sum(1 for e in entries if e.get("compliance_mapping", {}).get("eu_ai_act_article_12"))
        art12_pct = round((art12_count / total) * 100, 1)

        # Art. 14: escalation paths defined and triggered
        art14_compliant = all(
            e.get("compliance_mapping", {}).get("eu_ai_act_article_14")
            for e in entries
        )
        art14_escalations = sum(1 for e in entries if e.get("escalation"))

        return {
            "framework": "EU AI Act",
            "entries_evaluated": total,
            "article_12_coverage": f"{art12_pct}%",
            "article_12_detail": f"{art12_count}/{total} actions with complete audit trail",
            "article_14_compliant": art14_compliant,
            "article_14_detail": f"{art14_escalations} escalations triggered, oversight paths {'defined' if art14_compliant else 'MISSING'}",
        }

    elif framework == "gdpr":
        # Art. 22: automated decisions without human review
        art22_flags = sum(
            1 for e in entries
            if e.get("compliance_mapping", {}).get("gdpr_article_22")
        )

        # Art. 35: actions touching PII-classified data
        art35_flags = sum(
            1 for e in entries
            if e.get("compliance_mapping", {}).get("gdpr_article_35")
        )

        return {
            "framework": "GDPR",
            "entries_evaluated": total,
            "article_22_flags": art22_flags,
            "article_22_detail": f"{art22_flags} automated decisions without human review",
            "article_35_flags": art35_flags,
            "article_35_detail": f"{art35_flags} actions touching PII-classified data",
        }

    else:
        return {"framework": framework, "error": f"Unknown framework: {framework}. Use 'eu-ai-act' or 'gdpr'."}
