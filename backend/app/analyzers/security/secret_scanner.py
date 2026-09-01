import math
import re
from typing import List, Dict, Any, Optional


def shannon_entropy(data: str) -> float:
    """Calculates Shannon entropy to detect high-entropy secrets and avoid false positives."""
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy


class SecretRule:
    def __init__(self, name: str, pattern: str, severity: str = "CRITICAL", min_entropy: float = 3.0):
        self.name = name
        self.regex = re.compile(pattern)
        self.severity = severity
        self.min_entropy = min_entropy


SECRET_RULES: List[SecretRule] = [
    SecretRule(
        name="AWS Access Key ID",
        pattern=r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        severity="CRITICAL",
        min_entropy=3.0,
    ),
    SecretRule(
        name="AWS Secret Access Key",
        pattern=r"(?i)aws_secret_access_key\s*[:=]\s*['\"]([A-Za-z0-9/+=]{40})['\"]",
        severity="CRITICAL",
        min_entropy=4.2,
    ),
    SecretRule(
        name="GitHub Personal Access Token",
        pattern=r"gh[pousr]_[A-Za-z0-9_]{36,255}",
        severity="CRITICAL",
        min_entropy=3.5,
    ),
    SecretRule(
        name="OpenAI API Key",
        pattern=r"sk-[a-zA-Z0-9]{20,T3BlbkFJ[a-zA-Z0-9]{20,}",
        severity="CRITICAL",
        min_entropy=3.8,
    ),
    SecretRule(
        name="Generic Private Key",
        pattern=r"-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP)? PRIVATE KEY-----",
        severity="CRITICAL",
        min_entropy=0.0,
    ),
    SecretRule(
        name="JWT Token",
        pattern=r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+",
        severity="HIGH",
        min_entropy=4.0,
    ),
    SecretRule(
        name="Database Connection String with Password",
        pattern=r"(?i)(?:postgres|postgresql|mysql|mongodb|redis):\/\/[a-zA-Z0-9_]+:([^@\s'\"]{4,})@[a-zA-Z0-9_.-]+",
        severity="CRITICAL",
        min_entropy=2.8,
    ),
    SecretRule(
        name="Hardcoded High-Entropy API Secret",
        pattern=r"(?i)(?:api_key|apikey|secret_key|auth_token|client_secret)\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]",
        severity="HIGH",
        min_entropy=3.7,
    ),
    SecretRule(
        name="Slack Bot/User Token",
        pattern=r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}",
        severity="CRITICAL",
        min_entropy=3.5,
    ),
]


class SecretScanner:
    """
    Gitleaks-grade pattern and entropy secret detection engine.
    """

    @classmethod
    def scan_file(cls, file_path: str, content: str) -> List[Dict[str, Any]]:
        findings = []
        lines = content.splitlines()

        # Skip scanning files that are known test fixtures or lock files with hashes
        if any(skip in file_path.lower() for skip in ("package-lock.json", "yarn.lock", "poetry.lock", "cargo.lock")):
            return []

        for line_idx, line in enumerate(lines, start=1):
            # Avoid overly long generated lines (e.g. minified bundles)
            if len(line) > 2000:
                continue

            for rule in SECRET_RULES:
                matches = rule.regex.findall(line)
                for match in matches:
                    matched_str = match if isinstance(match, str) else match[0]
                    # Check entropy threshold to reduce false alarms on dummy test tokens
                    if rule.min_entropy > 0 and shannon_entropy(matched_str) < rule.min_entropy:
                        continue
                        
                    # Ignore obvious place-holders
                    if any(ph in matched_str.lower() for ph in ("your_api_key", "dummy_token", "placeholder", "changeme", "test_secret_xxx")):
                        continue

                    snippet = line.strip()
                    if len(snippet) > 200:
                        snippet = snippet[:197] + "..."

                    findings.append({
                        "severity": rule.severity,
                        "category": "SECURITY",
                        "title": f"Hardcoded Secret: {rule.name}",
                        "description": f"Potential unencrypted secret or credential exposed in source code ({rule.name}).",
                        "file_path": file_path,
                        "line_number": line_idx,
                        "code_snippet": snippet,
                        "impact": "Exposure of sensitive credentials or API keys can lead to unauthorized account access, data breaches, and infrastructure takeover.",
                        "recommendation": "Remove hardcoded credentials immediately. Rotate the exposed token and load secrets dynamically via environment variables or a Secret Manager (e.g., Vault, AWS Secrets Manager).",
                        "suggested_fix": f"# Replace with environment variable:\n# secret = os.getenv('{rule.name.upper().replace(' ', '_')}')",
                        "tool": "secret_scanner",
                        "confidence": "HIGH" if rule.min_entropy > 3.5 else "MEDIUM",
                    })

        return findings
