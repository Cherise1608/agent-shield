# Agent Shield — Beginner's Guide

A step-by-step guide to running your first governance scan with Agent Shield.

## What is Agent Shield?

Agent Shield is a CLI tool that scans your AI agent project and tells you how "governance-ready" it is. It checks for things like leaked secrets, missing logging, lack of human oversight, and poor documentation — then gives you a score from 0 to 100.

Every finding maps directly to real regulations (EU AI Act, GDPR, OWASP LLM Top 10), so you know exactly what to fix and why it matters.

## Install

```bash
pip install agent-shield
```

Or install from source:

```bash
git clone https://github.com/fluxai-dk/agent-shield.git
cd agent-shield
pip install -e .
```

Requires Python 3.10+. No external dependencies.

## Run your first scan

Point it at any project directory:

```bash
agent-shield scan /path/to/your-agent-project
```

Or scan the current directory:

```bash
agent-shield scan .
```

That's it. You'll get a colored terminal report with your score.

## Reading the results

The output is split into six categories, each with its own score:

| Category | What it checks |
|---|---|
| Secrets & Access Control | Exposed API keys, missing `.gitignore`, hardcoded passwords |
| Audit & Logging | Logging setup, trace IDs, observability tools |
| Human Oversight | Approval gates, kill switches, escalation logic |
| Data Classification | PII tagging, anonymization, consent patterns |
| Error Handling | Exception handling, retries, resource boundaries |
| Documentation | README, model cards, risk assessments, architecture docs |

Each finding is labeled:

- **CRITICAL** — Fix this before deploying. Example: an API key exposed in source code.
- **WARNING** — Not a blocker, but a real gap. Example: no structured logging.
- **PASS** — You're covered here. Example: `.env` is properly gitignored.

Every finding includes a **fix suggestion** and the **regulatory article** it relates to.

### Score interpretation

| Score | Rating | What it means |
|---|---|---|
| 80–100 | Governance Ready | Good to go for production |
| 60–79 | Partially Governed | Key controls exist, but gaps remain |
| 40–59 | Exposed | Significant governance gaps |
| 0–39 | Critical Exposure | Not ready for production |

The CLI exits with code `1` if your score is below 70%, making it easy to use as a CI gate.

## Pick a framework

By default, Agent Shield runs all checks. You can narrow the scan to a specific regulatory framework:

```bash
# EU AI Act compliance
agent-shield scan . --framework eu-ai-act

# GDPR compliance
agent-shield scan . --framework gdpr

# OWASP LLM Top 10
agent-shield scan . --framework owasp-llm

# NIST AI Risk Management Framework
agent-shield scan . --framework nist-ai-rmf
```

Each framework runs only the checks relevant to that regulation:

| Framework | Checks included |
|---|---|
| `all` (default) | All 6 categories |
| `eu-ai-act` | Human oversight, audit logging, error handling, documentation, data classification |
| `gdpr` | Secrets, data classification, audit logging, documentation |
| `owasp-llm` | Secrets, error handling, human oversight, audit logging |
| `nist-ai-rmf` | All 6 categories |

## Change the output format

The default output is colored text for your terminal. You can also get:

```bash
# JSON (for CI/CD pipelines or scripts)
agent-shield scan . --format json

# Markdown (for reports or documentation)
agent-shield scan . --format markdown
```

## Example: scanning a real project

Here's what a typical workflow looks like:

```bash
# 1. Scan your project
agent-shield scan ./my-agent --framework eu-ai-act

# 2. Read the findings — fix the CRITICALs first
#    e.g. "Exposed API key in src/config.py"
#    Fix: move the key to an environment variable

# 3. Re-scan to verify your fixes
agent-shield scan ./my-agent --framework eu-ai-act

# 4. Once you're above 70%, add it to your CI pipeline
```

## Add it to CI/CD

Agent Shield returns exit code `1` when the score is below 70%, so you can use it as a pipeline gate.

**GitHub Actions example:**

```yaml
- name: Governance scan
  run: |
    pip install agent-shield
    agent-shield scan . --framework eu-ai-act --format json
```

If the score drops below 70%, the step fails and the pipeline stops.

## Quick reference

```
agent-shield scan <path>                    # Scan with all checks
agent-shield scan <path> --framework gdpr   # Scan for GDPR only
agent-shield scan <path> --format json      # Output as JSON
agent-shield scan <path> --format markdown  # Output as Markdown
```

## What's next?

After your first scan:

1. **Fix CRITICALs first** — these are the highest-risk findings (leaked secrets, no logging).
2. **Add governance docs** — a `model-card.md` and `risk-assessment.md` go a long way.
3. **Set up structured logging** — libraries like `structlog` (Python) or `pino` (Node) boost your audit score.
4. **Add human oversight patterns** — approval gates before destructive actions, confidence thresholds for escalation.
5. **Run it in CI** — make governance scanning part of every pull request.

---

Built by [Flux AI](https://fluxai.dk)
