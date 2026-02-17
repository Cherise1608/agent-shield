"""Check for exposed secrets and access control issues."""
import re
from pathlib import Path

SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}', "API key"),
    (r'(?i)(secret|password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']{8,}', "Password/Secret"),
    (r'(?i)(token)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}', "Token"),
    (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API key"),
    (r'sk-ant-[a-zA-Z0-9\-]{32,}', "Anthropic API key"),
    (r'(?i)postgres(?:ql)?://[^\s"\']+', "Database connection string"),
    (r'(?i)mysql://[^\s"\']+', "Database connection string"),
    (r'(?i)mongodb(\+srv)?://[^\s"\']+', "Database connection string"),
    (r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*[^\s"\']+', "AWS credential"),
    (r'AKIA[0-9A-Z]{16}', "AWS access key ID"),
    (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', "Private key"),
]

SENSITIVE_FILES = {".env", ".env.local", ".env.production", ".env.staging"}

GOOD_PATTERNS = [
    r'os\.environ\.get\(',
    r'os\.getenv\(',
    r'process\.env\.',
    r'dotenv',
    r'vault',
    r'secret_?manager',
    r'key_?vault',
]

def check_secrets(project_path: Path, files: list[Path]) -> dict:
    """Check for exposed secrets and access control issues. Max 15 points."""
    score = 15
    findings = []
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".yaml", ".yml", ".toml", ".json"}
    secrets_found = []

    for f in files:
        if f.suffix not in code_extensions:
            continue
        if f.name in {".env.example", ".env.template"}:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        for pattern, secret_type in SECRET_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                rel_path = f.relative_to(project_path)
                secrets_found.append((rel_path, secret_type))

    if secrets_found:
        score -= 5
        locations = list({str(s[0]) for s in secrets_found})[:5]
        types = list({s[1] for s in secrets_found})
        findings.append({
            "severity": "critical",
            "category": "secrets",
            "title": "Potential secrets found in code",
            "detail": f"Found {len(secrets_found)} potential secret(s) ({', '.join(types)}) in: {', '.join(locations)}",
            "fix": "Move secrets to environment variables. Use a secrets manager for production.",
            "articles": ["GDPR Art. 32", "EU AI Act Art. 15"],
        })

    gitignore_path = project_path / ".gitignore"
    gitignore_content = ""
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text(errors="ignore")

    env_files_present = [f for f in files if f.name in SENSITIVE_FILES]
    env_in_gitignore = ".env" in gitignore_content

    if env_files_present and not env_in_gitignore:
        score -= 4
        findings.append({
            "severity": "critical",
            "category": "secrets",
            "title": ".env file not in .gitignore",
            "detail": f"Found {', '.join(f.name for f in env_files_present)} but .env is not in .gitignore.",
            "fix": "Add .env to .gitignore immediately. Check git history for previously committed secrets.",
            "articles": ["GDPR Art. 32"],
        })
    elif env_in_gitignore:
        findings.append({
            "severity": "pass",
            "category": "secrets",
            "title": ".gitignore covers secret files",
            "detail": ".env is listed in .gitignore.",
        })

    uses_env_vars = False
    uses_secret_manager = False

    for f in files:
        if f.suffix not in code_extensions:
            continue
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue

        for pattern in GOOD_PATTERNS[:3]:
            if re.search(pattern, content):
                uses_env_vars = True
        for pattern in GOOD_PATTERNS[3:]:
            if re.search(pattern, content):
                uses_secret_manager = True

    if not uses_env_vars:
        score -= 3
        findings.append({
            "severity": "warning",
            "category": "secrets",
            "title": "No environment variable usage detected",
            "detail": "No patterns for os.environ, os.getenv, or process.env found.",
            "fix": "Use environment variables for all configuration secrets.",
            "articles": ["GDPR Art. 32"],
        })

    if uses_secret_manager:
        findings.append({
            "severity": "pass",
            "category": "secrets",
            "title": "Secret management pattern detected",
            "detail": "Found usage of vault, secret manager, or similar.",
        })

    if not gitignore_path.exists():
        score -= 3
        findings.append({
            "severity": "warning",
            "category": "secrets",
            "title": "No .gitignore file found",
            "detail": "Project has no .gitignore, increasing risk of accidental secret exposure.",
            "fix": "Add a .gitignore file covering .env, credentials, and build artifacts.",
            "articles": [],
        })

    return {
        "name": "Secrets & Access",
        "icon": "🔐",
        "score": max(0, score),
        "max_score": 15,
        "findings": findings,
    }
