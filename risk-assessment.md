# Risk Assessment — agent-shield

## System Description

agent-shield is a CLI tool that performs static analysis on AI agent project directories. It reads source files, checks for governance patterns, and produces a scored report.

## Risk Classification

Under the EU AI Act, agent-shield itself is a **development tool** and is not classified as a high-risk AI system. However, the projects it scans may fall under high-risk categories, making accurate scan results important.

## Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| False negatives (missed issues) | Medium | High | Pattern library is regularly updated; users are advised not to rely solely on automated scans. |
| False positives (incorrect flags) | Medium | Low | Findings include actionable detail so users can verify before acting. |
| Secret exposure in scan output | Low | High | Scanner reports file locations, not secret values. Output is local-only by default. |
| Stale compliance advice | Medium | Medium | Regulatory references are pinned to specific articles and reviewed on each release. |

## Mitigations in Place

- **Human oversight:** Scan results are advisory — no automated remediation is performed.
- **Transparency:** Each finding cites the relevant regulatory article.
- **Minimal permissions:** The tool requires only read access to the scanned directory.

## Review Schedule

This risk assessment should be reviewed when:
- New check categories are added.
- Referenced regulations are updated.
- The tool gains capabilities beyond static analysis (e.g., auto-fix).
