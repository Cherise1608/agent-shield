"""Governance framework definitions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Framework:
    name: str
    description: str
    checks: list[str] = field(default_factory=list)


FRAMEWORKS: dict[str, Framework] = {
    "all": Framework(
        name="all",
        description="Run every available check.",
        checks=[],  # empty means run all
    ),
    "eu-ai-act": Framework(
        name="eu-ai-act",
        description="EU Artificial Intelligence Act compliance checks.",
        checks=[
            "check_human_oversight",
            "check_audit_logging",
            "check_error_handling",
            "check_documentation",
            "check_data_classification",
        ],
    ),
    "gdpr": Framework(
        name="gdpr",
        description="GDPR data-protection focused checks.",
        checks=[
            "check_secrets",
            "check_data_classification",
            "check_audit_logging",
            "check_documentation",
        ],
    ),
    "owasp-llm": Framework(
        name="owasp-llm",
        description="OWASP Top 10 for LLM Applications.",
        checks=[
            "check_secrets",
            "check_error_handling",
            "check_human_oversight",
            "check_audit_logging",
        ],
    ),
    "nist-ai-rmf": Framework(
        name="nist-ai-rmf",
        description="NIST AI Risk Management Framework.",
        checks=[
            "check_human_oversight",
            "check_audit_logging",
            "check_error_handling",
            "check_documentation",
            "check_data_classification",
            "check_secrets",
        ],
    ),
}


def get_framework(name: str) -> Framework:
    """Return a Framework by name, defaulting to 'all'."""
    return FRAMEWORKS.get(name, FRAMEWORKS["all"])
