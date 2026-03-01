# agent-shield 🛡️

Governance readiness scanner for AI agent projects.

Scan your repo. Get a score. Know what to fix before production.

```bash
pip install agent-shield
agent-shield scan .
```

```
agent-shield v0.1.0 — Governance Readiness Scanner

Scanning: /path/to/your-agent-project
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CATEGORY                        SCORE
──────────────────────────────────────
🔐 Secrets & Access             8/15
📋 Audit & Logging              3/20
👤 Human Oversight              0/20
🗂️ Data Classification          5/15
⚠️ Error Handling               12/15
📄 Documentation                7/15

──────────────────────────────────────
TOTAL                           35/100
RATING                          ⚠️ Exposed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FINDINGS:

[CRITICAL] No audit logging detected
  → No structured logging of agent decisions found.
  → EU AI Act Article 12 requires automatic logging
    for high-risk AI systems.
  → Fix: Add decision logging middleware.

[CRITICAL] No human-in-the-loop pattern detected
  → No approval gate or escalation logic found.
  → EU AI Act Article 14 requires human oversight
    for high-risk systems.
  → Fix: Add human approval gate before external actions.

[WARNING] .env file contains potential secrets
  → Found: OPENAI_API_KEY, DATABASE_URL
  → Ensure .env is in .gitignore and secrets are
    not committed to version history.

[WARNING] No data classification markers found
  → Agent processes unclassified data by default.
  → GDPR Article 25 requires data protection by design.
  → Fix: Add data classification to your schema.

[PASS] Error handling detected in agent outputs
[PASS] API key rotation pattern found
[PASS] .gitignore covers common secret files
```

## Why

Every agent framework gives you tools to **build**.
None of them tell you if what you built is **ready for production**.

EU AI Act enforcement starts August 2026. GDPR already applies.
Your agent project either passes an audit or it doesn't.

`agent-shield` tells you where you stand — before someone else does.

## What it checks

### 🔐 Secrets & Access (15 points)
- Exposed API keys and credentials in code
- `.env` files committed or unprotected
- `.gitignore` coverage for secret files
- Hardcoded connection strings

### 📋 Audit & Logging (20 points)
- Structured logging of agent decisions
- Trace ID / correlation ID patterns
- Input/output logging on agent calls
- Timestamp and session tracking

### 👤 Human Oversight (20 points)
- Human-in-the-loop approval gates
- Escalation logic for high-risk decisions
- Confirmation patterns before external actions
- Override / kill switch mechanisms

### 🗂️ Data Classification (15 points)
- PII detection patterns in data handling
- Data classification markers or schemas
- GDPR-relevant processing documentation
- Consent or legal basis references

### ⚠️ Error Handling (15 points)
- Try/catch on agent tool calls
- Fallback logic for failed LLM calls
- Graceful degradation patterns
- Error logging with context

### 📄 Documentation (15 points)
- README with system description
- Architecture or data flow documentation
- Risk assessment or DPIA references
- Deployment and rollback procedures

### ⚖️ Art. 14 Human Oversight — Automated Decisions (15 points)
- LLM output used directly in decision conditionals without human validation
- Auto-approve / auto-execute functions with no human review companion
- Agent output piped directly to system actions (DB writes, API calls, emails)
- Automated decision paths with no human checkpoint

### 📋 Art. 22 Accountability (15 points)
- Agent/tool configs with no owner or responsible_party declared
- Multi-agent orchestration with no escalation path or fallback handler
- Silent error handlers on agent decision paths (except: pass)
- Agent output to external systems with no schema or type validation
- No audit trail (timestamp, agent_id, input/output hash, decision rationale)

## Scoring

| Score | Rating | Meaning |
|-------|--------|---------|
| 80-100% | ✅ Governance Ready | Production-ready with governance controls |
| 60-79% | 🔶 Partially Governed | Key controls in place, gaps remain |
| 40-59% | ⚠️ Exposed | Significant governance gaps |
| 0-39% | 🔴 Critical Exposure | Not ready for production deployment |

Total possible score: **130 points** across 8 check categories.

## Usage

### Basic scan
```bash
agent-shield scan .
```

### Scan with specific framework mapping
```bash
agent-shield scan . --framework eu-ai-act
agent-shield scan . --framework gdpr
agent-shield scan . --framework owasp-llm
agent-shield scan . --framework nist-ai-rmf
```

### Output formats
```bash
agent-shield scan . --format text        # Default
agent-shield scan . --format json        # Machine-readable
agent-shield scan . --format markdown    # For docs/reports
```

### CI/CD integration

The CLI exits with code `1` if the score is below 70%, so it works as a pipeline gate out of the box.

#### GitHub Actions example
```yaml
name: Governance Check
on: [push, pull_request]

jobs:
  governance-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install agent-shield
      - run: agent-shield scan . --framework eu-ai-act --format json
```

## Regulatory mapping

agent-shield maps findings directly to regulatory articles:

- **EU AI Act** — Articles 9 (Risk Management), 11 (Technical Documentation), 12 (Record-Keeping), 13 (Transparency), 14 (Human Oversight), 15 (Robustness), 22 (Accountability)
- **GDPR** — Articles 5 (Processing Principles), 5(2) (Accountability), 22 (Automated Decision-Making), 25 (Data Protection by Design), 32 (Security), 35 (DPIA)

Each finding includes the specific article reference and a concrete fix suggestion.

## Roadmap

**v0.1** — Static scanner (current)
- Repo scanning with governance scoring
- EU AI Act and GDPR framework mapping
- CLI with text, JSON, and markdown output

**v0.2** — Fix guide & runtime monitor
- `--fix-guide` flag generating actionable fix instructions with code snippets
- Lightweight middleware for agent decision logging
- Webhook alerts on governance drift

**v0.3** — Policy engine
- Declarative permission rules for agents (YAML)
- Action-level access control
- Approval workflows for high-risk operations

## Install

```bash
pip install agent-shield
```

Or from source:
```bash
git clone https://github.com/Cherise1608/agent-shield.git
cd agent-shield
pip install -e .
```

## Built by

[Flux AI](https://fluxai.dk) — Agentic AI with Governance Built In.

Governance scanning for teams and solo developers shipping AI agents

## License

This project is licensed under the [Business Source License 1.1](LICENSE).

- **Non-competing use** is permitted immediately.
- **Competing use** (offering a governance readiness scanner or compliance tool for AI agents as a service) is not permitted before the Change Date.
- On **2030-02-17**, the license converts to **MIT**.

See [LICENSE](LICENSE) for full terms.
