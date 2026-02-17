"""Check for data classification and PII handling practices."""
import re
from pathlib import Path

CLASSIFICATION_PATTERNS = [
    (r'(?i)data[_\-]?classif(y|ication)', "Data classification logic"),
    (r'(?i)pii|personally[_\-]?identifiable', "PII reference"),
    (r'(?i)sensitive[_\-]?data|confidential', "Sensitive data label"),
    (r'(?i)data[_\-]?category|data[_\-]?level|data[_\-]?tier', "Data categorisation"),
]

PRIVACY_PATTERNS = [
    (r'(?i)anonymiz(e|ation)|pseudonymiz(e|ation)', "Anonymisation/pseudonymisation"),
    (r'(?i)redact|mask|obfuscate', "Data redaction"),
    (r'(?i)encrypt|AES|RSA|fernet', "Encryption usage"),
    (r'(?i)data[_\-]?retention|retention[_\-]?polic', "Retention policy"),
    (r'(?i)right[_\-]?to[_\-]?erasure|right[_\-]?to[_\-]?forget|data[_\-]?deletion', "Right to erasure"),
]

PRIVACY_DOC_FILES = {
    "privacy.md", "privacy-policy.md", "data-classification.md",
    "data_classification.md", "dpia.md", "pia.md",
}

CONSENT_PATTERNS = [
    (r'(?i)consent|opt[_\-]?(in|out)', "Consent mechanism"),
    (r'(?i)gdpr|data[_\-]?protect', "GDPR reference"),
    (r'(?i)data[_\-]?processing[_\-]?agreement|dpa', "DPA reference"),
]


def check_data_classification(project_path: Path, files: list[Path]) -> dict:
    """Check for data classification and PII handling. Max 15 points."""
    score = 0
    findings = []
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".yaml", ".yml"}

    has_classification = False
    has_privacy_tech = False
    has_privacy_doc = False
    has_consent = False

    for f in files:
        if f.name.lower() in PRIVACY_DOC_FILES:
            has_privacy_doc = True

        if f.suffix not in code_extensions:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        for pattern, name in CLASSIFICATION_PATTERNS:
            if re.search(pattern, content):
                has_classification = True

        for pattern, name in PRIVACY_PATTERNS:
            if re.search(pattern, content):
                has_privacy_tech = True

        for pattern, name in CONSENT_PATTERNS:
            if re.search(pattern, content):
                has_consent = True

    if has_classification:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "data_classification",
            "title": "Data classification logic detected",
            "detail": "Found data classification, PII labelling, or sensitivity tagging in code.",
        })
    else:
        findings.append({
            "severity": "critical",
            "category": "data_classification",
            "title": "No data classification detected",
            "detail": "No PII labelling, data categorisation, or sensitivity tagging found.",
            "fix": "Tag data fields with classification levels (public, internal, confidential, restricted).",
            "articles": ["EU AI Act Art. 10", "GDPR Art. 5"],
        })

    if has_privacy_tech:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "data_classification",
            "title": "Privacy-preserving techniques detected",
            "detail": "Found anonymisation, pseudonymisation, redaction, or encryption patterns.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "data_classification",
            "title": "No privacy-preserving techniques detected",
            "detail": "No anonymisation, pseudonymisation, redaction, or encryption found.",
            "fix": "Apply data minimisation: anonymise or pseudonymise PII before processing.",
            "articles": ["GDPR Art. 25", "GDPR Art. 32"],
        })

    if has_privacy_doc:
        score += 4
        findings.append({
            "severity": "pass",
            "category": "data_classification",
            "title": "Privacy documentation found",
            "detail": "Found a privacy policy, DPIA, or data classification document.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "data_classification",
            "title": "No privacy documentation found",
            "detail": "No privacy.md, dpia.md, or data-classification.md found.",
            "fix": "Add a DPIA or data classification document describing what data is collected, stored, and processed.",
            "articles": ["GDPR Art. 35", "EU AI Act Art. 9"],
        })

    if has_consent:
        score += 3
        findings.append({
            "severity": "pass",
            "category": "data_classification",
            "title": "Consent / GDPR patterns detected",
            "detail": "Found consent mechanism, opt-in/opt-out, or GDPR references.",
        })
    else:
        findings.append({
            "severity": "warning",
            "category": "data_classification",
            "title": "No consent mechanisms detected",
            "detail": "No consent, opt-in/opt-out, or GDPR references found in code.",
            "fix": "Add explicit consent collection before processing personal data.",
            "articles": ["GDPR Art. 6", "GDPR Art. 7"],
        })

    return {
        "name": "Data Classification",
        "icon": "📊",
        "score": min(score, 15),
        "max_score": 15,
        "findings": findings,
    }
