"""Check for governance-relevant documentation."""
from pathlib import Path

STANDARD_DOCS = {
    "readme.md": "Project overview",
    "contributing.md": "Contribution guidelines",
    "changelog.md": "Change history",
    "license": "License file",
}

GOVERNANCE_DOCS = {
    "model-card.md": "Model card",
    "model_card.md": "Model card",
    "system-card.md": "System card",
    "data-sheet.md": "Data sheet",
    "risk-assessment.md": "Risk assessment",
    "risk_assessment.md": "Risk assessment",
    "impact-assessment.md": "Impact assessment",
    "dpia.md": "DPIA",
    "pia.md": "PIA",
    "transparency.md": "Transparency notice",
    "responsible-ai.md": "Responsible AI policy",
}

ARCHITECTURE_DOCS = {
    "architecture.md": "Architecture doc",
    "design.md": "Design doc",
    "adr": "Architecture decision records (dir)",
    "docs": "Documentation directory",
}


def check_documentation(project_path: Path, files: list[Path]) -> dict:
    """Check for governance-relevant documentation. Max 15 points."""
    score = 0
    findings = []

    filenames = {f.name.lower() for f in files}
    dirnames = {d.name.lower() for d in project_path.iterdir() if d.is_dir()}

    # Standard project docs (max 4 pts)
    present = [doc for doc in STANDARD_DOCS if doc in filenames]
    missing = [doc for doc in STANDARD_DOCS if doc not in filenames]

    if not missing:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "documentation",
            "title": "All standard project docs present",
            "detail": f"Found: {', '.join(present)}.",
        })
    elif len(missing) <= 2:
        score += 2
        findings.append({
            "severity": "warning",
            "category": "documentation",
            "title": f"Missing standard docs: {', '.join(missing)}",
            "detail": f"Found {len(present)}/{len(STANDARD_DOCS)} standard docs.",
            "fix": f"Add: {', '.join(missing)}.",
            "articles": [],
        })
    else:
        findings.append({
            "severity": "critical",
            "category": "documentation",
            "title": f"Missing key documentation: {', '.join(missing)}",
            "detail": f"Only {len(present)}/{len(STANDARD_DOCS)} standard docs found.",
            "fix": f"Add: {', '.join(missing)}.",
            "articles": [],
        })

    # Governance docs (max 6 pts)
    gov_present = [doc for doc in GOVERNANCE_DOCS if doc in filenames]
    if gov_present:
        score += 6
        names = [GOVERNANCE_DOCS[d] for d in gov_present]
        findings.append({
            "severity": "pass",
            "category": "documentation",
            "title": "Governance documentation found",
            "detail": f"Found: {', '.join(names)}.",
        })
    else:
        findings.append({
            "severity": "critical",
            "category": "documentation",
            "title": "No governance documentation",
            "detail": "No model card, risk assessment, DPIA, or transparency notice found.",
            "fix": "Add a model card (model-card.md) and risk assessment (risk-assessment.md) for EU AI Act compliance.",
            "articles": ["EU AI Act Art. 11", "EU AI Act Art. 13"],
        })

    # Architecture docs (max 3 pts)
    arch_present = [d for d in ARCHITECTURE_DOCS if d in filenames or d in dirnames]
    if arch_present:
        score += 3
        findings.append({
            "severity": "pass",
            "category": "documentation",
            "title": "Architecture documentation found",
            "detail": f"Found: {', '.join(arch_present)}.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "documentation",
            "title": "No architecture documentation",
            "detail": "No architecture.md, design.md, ADR directory, or docs/ found.",
            "fix": "Add architecture documentation describing system design and agent interaction patterns.",
            "articles": ["EU AI Act Art. 11"],
        })

    # Inline docstrings check (max 2 pts)
    py_files_with_docstrings = 0
    py_files_total = 0
    for f in files:
        if f.suffix != ".py":
            continue
        py_files_total += 1
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue
        if '"""' in content or "'''" in content:
            py_files_with_docstrings += 1

    if py_files_total > 0:
        ratio = py_files_with_docstrings / py_files_total
        if ratio >= 0.5:
            score += 2
            findings.append({
                "severity": "pass",
                "category": "documentation",
                "title": "Good docstring coverage",
                "detail": f"{py_files_with_docstrings}/{py_files_total} Python files contain docstrings.",
            })
        else:
            findings.append({
                "severity": "warning",
                "category": "documentation",
                "title": "Low docstring coverage",
                "detail": f"Only {py_files_with_docstrings}/{py_files_total} Python files contain docstrings.",
                "fix": "Add module and function docstrings for auditability.",
                "articles": ["EU AI Act Art. 11"],
            })

    return {
        "name": "Documentation",
        "icon": "📝",
        "score": min(score, 15),
        "max_score": 15,
        "findings": findings,
    }
