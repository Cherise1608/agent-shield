# Technical Architecture Document: Agent Shield

**Version:** 0.3.0
**Dato:** 2026-03-27
**Forfatter:** Jesca Martaeng, FluxAI
**Repo:** https://github.com/fluxai-dk/agent-shield

---

## 1. Formål

Agent Shield er en governance readiness scanner og runtime audit-platform for AI-agent-projekter. Den scanner kodebaser for compliance-parathed, håndhæver governance-regler ved runtime, og producerer revisionssikre audit trails.

### Plads i økosystemet

```
┌──────────────────────────────────────────────────┐
│                  Governance Stack                 │
│                                                   │
│   Airlock (governance.yaml)    ← Policy-lag       │
│          │                                        │
│          ▼                                        │
│   Agent Shield (scanner)       ← Analyse-lag      │
│          │                                        │
│          ▼                                        │
│   Agent Shield (report)        ← Accountability   │
│          │                        (NYT LAG)       │
│          ▼                                        │
│   governance-report.json       ← Audit ledger     │
└──────────────────────────────────────────────────┘
```

---

## 2. Arkitekturoverblik

```
agent-shield/
├── agent_shield/
│   ├── __init__.py              # Version
│   ├── cli.py                   # CLI entrypoint (scan, report, compliance, verify)
│   ├── scanner.py               # Kodebase-scanning og score-beregning
│   ├── frameworks.py            # Framework-definitioner (EU AI Act, GDPR, OWASP, NIST, Healthcare)
│   ├── formatters.py            # Output: text, json, markdown
│   ├── report.py                # Governance reporting og audit ledger (NYT)
│   ├── checks/
│   │   ├── secrets.py           # Hemmeligheder i kodebase
│   │   ├── audit_logging.py     # Audit-logging patterns
│   │   ├── human_oversight.py   # Human-in-the-loop patterns
│   │   ├── data_classification.py  # Data-klassifikation
│   │   ├── error_handling.py    # Fejlhåndtering
│   │   ├── documentation.py     # Dokumentation
│   │   ├── art14_human_oversight.py  # EU AI Act Art. 14
│   │   └── art22_accountability.py   # GDPR Art. 22
│   └── autonomous/              # Autonomi-relaterede checks
├── docs/
│   └── TAD.md                   # Denne fil
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## 3. Lag-arkitektur

Agent Shield har tre lag:

### 3.1 Analyse-lag (scan)
Statisk scanning af kodebaser mod governance-frameworks.

```
$ agent-shield scan . --framework eu-ai-act
```

- Kører check-moduler mod filsystemet
- Scorer hvert check (score/max_score)
- Aggregerer til samlet compliance-procent
- CI-gate: exit 0 ved ≥70%, exit 1 ellers

### 3.2 Reporting-lag (report) — NYT
Runtime audit ledger med chain integrity.

```
$ agent-shield report --last 24h
$ agent-shield compliance --framework eu-ai-act
$ agent-shield compliance --framework gdpr
$ agent-shield verify
```

- Append-only ledger (`governance-report.json`)
- Hver entry hashed med sha256 af forrige entry (blockchain-lignende kæde)
- Compliance mapping per entry (EU AI Act Art. 12/14, GDPR Art. 22/35)
- Governance status: ENFORCED / DEGRADED / UNMONITORED

### 3.3 Framework-lag
Definerer hvilke checks der tilhører hvilke regulatoriske frameworks.

| Framework | Checks |
|-----------|--------|
| `eu-ai-act` | human_oversight, audit_logging, error_handling, documentation, data_classification, art14, art22 |
| `gdpr` | secrets, data_classification, audit_logging, documentation, art22 |
| `owasp-llm` | secrets, error_handling, human_oversight, audit_logging |
| `nist-ai-rmf` | Alle checks |
| `healthcare` | Provenance, audit, oversight, data_classification, art14, art22, documentation |

---

## 4. Governance Reporting (Nyt lag — detaljer)

### 4.1 Ledger-entry struktur

Hver entry i `governance-report.json`:

```json
{
  "timestamp": "2026-03-27T14:30:00+00:00",
  "agent_name": "code-agent",
  "action_attempted": "Write .env",
  "policy_matched": "authorization.protected_paths",
  "result": "BLOCKED",
  "exit_code": 2,
  "drift_score": 0.0,
  "escalation": false,
  "compliance_mapping": {
    "eu_ai_act_article_12": true,
    "eu_ai_act_article_14": true,
    "gdpr_article_22": false,
    "gdpr_article_35": false
  },
  "previous_hash": "a1b2c3...",
  "entry_hash": "d4e5f6..."
}
```

### 4.2 Chain integrity

```
Entry 0: hash = sha256("genesis")
Entry 1: hash = sha256(entry_0.hash + canonical_json(entry_1))
Entry N: hash = sha256(entry_N-1.hash + canonical_json(entry_N))
```

Verificeres med `agent-shield verify`. Hvis én entry ændres, bryder kæden.

### 4.3 Compliance mapping

| Felt | Regulering | Trigger |
|------|-----------|---------|
| `eu_ai_act_article_12` | Logging og sporbarhed | Altid true (entry eksisterer) |
| `eu_ai_act_article_14` | Human oversight | True hvis eskalering eller oversight tilgængelig |
| `gdpr_article_22` | Automatiserede beslutninger | True hvis ALLOWED uden human review |
| `gdpr_article_35` | DPIA-relevant handling | True hvis PII-data berøres |

### 4.4 Governance status

| Status | Betingelse |
|--------|-----------|
| **ENFORCED** | Blokeringer sker, drift eskaleres |
| **DEGRADED** | Drift detekteret (>0.3) uden eskalering |
| **UNMONITORED** | Ingen entries i ledger |

### 4.5 Summary output

```
agent-shield report
====================================================
  Total actions evaluated:   6
  Actions blocked:           3
  Actions allowed:           3
  Drift events (>0.3):       1
  Escalations triggered:     1
====================================================
  Governance status:         ENFORCED
```

### 4.6 Compliance output

```
agent-shield compliance  |  EU AI Act
====================================================
  Entries evaluated: 6
  Art. 12 coverage:    100.0% (6/6 actions with complete audit trail)
  Art. 14 compliant:   Yes (1 escalations triggered, oversight paths defined)
====================================================

agent-shield compliance  |  GDPR
====================================================
  Entries evaluated: 6
  Art. 22 flags:       1 (1 automated decisions without human review)
  Art. 35 flags:       2 (2 actions touching PII-classified data)
====================================================
```

---

## 5. Emergency Mode (Nyt lag — infrastruktur-beredskab)

### 5.1 Trusselsmodel

Når en virksomheds primære platform går ned, stopper AI-agenter **ikke** automatisk. De kører videre — uden monitoring, uden eskalationskanaler, uden human oversight. Dette er en direkte violation af:

- **EU AI Act Art. 14** — human oversight skal være tilgængeligt
- **EU AI Act Art. 9** — risikostyringssystemet skal være operationelt

### 5.2 Kommando

```
$ agent-shield status --emergency --governance governance.yaml
```

### 5.3 Hvad den checker

Læser `delegation.escalation` fra governance.yaml. Hver kanal kan have et `endpoint` felt:

| Endpoint-type | Eksempel | Check-metode |
|--------------|---------|--------------|
| HTTP/HTTPS | `https://hooks.slack.com/...` | HTTP HEAD request |
| TCP | `tcp://mattermost.internal:443` | TCP socket connect |
| Proces | `process://rocketchat` | pgrep |
| Fil/socket | `file:///var/run/escalation.sock` | Fil-eksistens + skrivbarhed |
| (ingen) | — | Antaget utilgængelig |
| `abort` | — | Altid tilgængelig (built-in) |

### 5.4 Governance.yaml endpoint-konfiguration

```yaml
delegation:
  escalation:
    - channel: human_review
      trigger: threshold_reached
      endpoint: https://hooks.slack.com/services/T00/B00/xxx
    - channel: backup_comms
      trigger: primary_down
      endpoint: https://rocketchat.company.com/api/v1/channels.list
    - channel: abort
      trigger: critical_violation
```

### 5.5 Exit codes

| Exit | Status | Betydning |
|------|--------|-----------|
| 0 | NOMINAL | Alle oversight-kanaler operationelle |
| 1 | DEGRADED | Nogle kanaler nede, oversight stadig mulig |
| 2 | EMERGENCY | Alle human oversight-kanaler nede |

### 5.6 Output eksempel (emergency)

```
agent-shield status --emergency
========================================================
  Timestamp:    2026-03-27T20:39:57+00:00
  Governance:   governance.yaml
  Fail mode:    closed

  Escalation Channels
  ----------------------------------------
  [X] human_review         DOWN
      endpoint: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      detail:   Unreachable: Not Found
  [X] backup_comms         DOWN
      endpoint: https://rocketchat.example.com/api/v1/channels.list
      detail:   Unreachable: No address associated with hostname

  Assessment
  ----------------------------------------
  Human oversight available:  NO
  Governance intact:          NO
  Action: EMERGENCY — all human oversight channels unreachable.
          Switch to fail-closed. Halt all autonomous agents until
          communication is restored.

  Regulatory Impact
  ----------------------------------------
  EU AI Act Art. 9: AT RISK — governance prerequisites degraded
  EU AI Act Art. 14: VIOLATION — human oversight unreachable
========================================================
```

### 5.7 Integration med IT-beredskab

Emergency mode bygger bro mellem AI-governance og IT-nødberedskab:

```
Primær platform (Teams/Slack) → NEDE
        │
        ▼
agent-shield status --emergency → EMERGENCY (exit 2)
        │
        ▼
Backup-platform (Rocket.Chat/Mattermost) → tjekkes automatisk
        │
        ├── UP   → DEGRADED (exit 1), agenter fortsætter med reduceret autonomi
        └── DOWN → EMERGENCY (exit 2), alle agenter stoppes
```

Spørgsmålet "hvad gør vores agenter når Teams går ned?" har nu et svar.

---

## 6. Dataflow

### 5.1 Scan (statisk analyse)
```
$ agent-shield scan .
        │
        ▼
  Indsaml filer (ekskl. vendor/node_modules)
        │
        ▼
  Kør check-moduler mod filerne
        │
        ▼
  Score per check → aggregeret procent
        │
        ├── ≥70% → exit 0 (CI pass)
        └── <70% → exit 1 (CI fail)
```

### 5.2 Report (runtime audit)
```
  Airlock enforce.sh → blokerer/tillader tool call
        │
        ▼
  create_entry() → bygger entry med compliance mapping
        │
        ▼
  append_entry() → sha256-kæder til forrige entry
        │
        ▼
  governance-report.json (append-only)
        │
        ▼
  agent-shield report    → summary
  agent-shield compliance → regulatory mapping
  agent-shield verify    → chain integrity check
```

---

## 6. CLI Commands

| Command | Formål | Output |
|---------|--------|--------|
| `agent-shield scan [path]` | Statisk governance-scanning | Score, findings, CI exit code |
| `agent-shield report --last 24h` | Runtime audit summary | Blocked/allowed/drift/status |
| `agent-shield compliance --framework eu-ai-act` | EU AI Act compliance | Art. 12 coverage, Art. 14 status |
| `agent-shield compliance --framework gdpr` | GDPR compliance | Art. 22 flags, Art. 35 flags |
| `agent-shield verify` | Ledger-integritet | Chain PASS/FAIL |
| `agent-shield status --emergency` | Escalation channel health check | NOMINAL/DEGRADED/EMERGENCY |

Alle commands understøtter `--format json` for maskinlæsbar output.

---

## 7. Sikkerhedsmodel

- **Append-only ledger** — entries kan kun tilføjes, ikke ændres
- **SHA256 chain integrity** — manipulation af én entry bryder kæden
- **Compliance mapping per entry** — regulatory sporbarhed på handlingsniveau
- **Drift detection** — score >0.3 markerer adfærdsafvigelse
- **Governance status** — automatisk degradering ved uadresseret drift
- **Zero cloud dependencies** — alt kører lokalt, ingen data forlader maskinen
- **Emergency mode** — detekterer når eskalationskanaler er nede og anbefaler fail-closed

---

## 8. Integration med Airlock

```
governance.yaml (Airlock)        → Definerer reglerne
hooks/enforce.sh (Airlock)       → Håndhæver ved runtime (exit 0/2)
report.py (Agent Shield)         → Logger hvad der skete
governance-report.json           → Immutable audit trail
agent-shield compliance          → Regulatory rapportering
agent-shield status --emergency  → Er governance-forudsætningerne intakte?
```

Airlock uden Agent Shield er en policy-dokument.
Agent Shield uden Airlock er en scanner.
Sammen er de et governance-system med enforcement, audit, og compliance.

---

## 9. Licens

- **BSL 1.1** konverterer til Apache 2.0 den 2030-03-27
- Kommerciel licens: info@fluxai.dk

---

## 10. Relaterede ressourcer

- Agent Shield: https://github.com/fluxai-dk/agent-shield
- Airlock spec: https://github.com/Cherise1608/airlock
- DARMA framework: https://fluxai.dk/darma
- Product: https://fluxai.dk/agent-shield
