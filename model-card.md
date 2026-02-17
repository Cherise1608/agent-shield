# Model Card — agent-shield

## Overview

agent-shield is a static analysis tool that scans AI agent projects for governance readiness. It does not contain or deploy a machine-learning model itself; it evaluates whether agent projects meet compliance requirements under the EU AI Act, GDPR, and related frameworks.

## Intended Use

- **Primary users:** Developers and compliance teams building AI agent systems.
- **Task:** Automated governance auditing — checking for secrets exposure, logging, human oversight, data classification, error handling, and documentation.
- **Deployment:** CLI tool run locally or in CI/CD pipelines.

## Scope and Limitations

- Static analysis only — does not execute or interact with the scanned project at runtime.
- Pattern-based detection may produce false positives or miss obfuscated issues.
- Does not replace a full legal or compliance review.

## Ethical Considerations

- The tool encourages responsible AI development by surfacing governance gaps early.
- Scan results should be reviewed by a human before making compliance claims.

## References

- EU AI Act: Articles 9, 11, 12, 13, 15, 18, 19
- GDPR: Articles 5, 25, 32, 35
