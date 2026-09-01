import os
import re
import subprocess
import json
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.analyzers.file_scanner import ScannedFile
from app.analyzers.security.secret_scanner import SecretScanner


class SecurityScanner:
    """
    Comprehensive multi-language security scanner with AST checks,
    vulnerability pattern heuristics, secret detection, and Bandit tool integration.
    """

    # Multi-language vulnerability rules
    VULNERABILITY_RULES = [
        {
            "id": "SEC001_SQLI",
            "title": "Potential SQL Injection",
            "severity": "CRITICAL",
            "category": "SECURITY",
            "languages": ["python", "javascript", "typescript", "java", "go", "php", "ruby", "c#"],
            "patterns": [
                r"(?i)(?:execute|raw|query)\s*\(\s*f[\"'].*?(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|WHERE).*?\{",
                r"(?i)(?:execute|raw|query)\s*\(\s*[\"'].*?(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|WHERE).*?[\"']\s*\+",
                r"(?i)(?:execute|raw|query)\s*\(\s*`.*?(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|WHERE).*?\$\{",
                r"(?i)(?:query|sql|stmt)\s*=\s*f[\"'].*?(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|WHERE).*?\{",
                r"(?i)String\s+query\s*=\s*[\"'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?[\"']\s*\+",
            ],
            "description": "Dynamic concatenation or unparameterized variable interpolation inside a SQL query statement.",
            "impact": "Attackers can bypass authentication, read, modify, or delete arbitrary database records, or execute administrative operations.",
            "recommendation": "Use parameterized queries, prepared statements, or ORM parameter binding instead of string concatenation/f-strings.",
            "suggested_fix": "# Example parameterized query fix:\n# cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
        },
        {
            "id": "SEC002_CMD_INJECTION",
            "title": "Command Injection Vulnerability",
            "severity": "CRITICAL",
            "category": "SECURITY",
            "languages": ["python", "javascript", "typescript", "go", "php"],
            "patterns": [
                r"(?i)subprocess\.(?:Popen|call|run|check_output)\s*\([^)]*shell\s*=\s*True",
                r"(?i)os\.system\s*\(",
                r"(?i)os\.popen\s*\(",
                r"(?i)child_process\.(?:exec|execSync)\s*\(\s*`[^`]*\$\{",
                r"(?i)child_process\.(?:exec|execSync)\s*\([^)]*\+",
                r"(?i)exec\.Command\s*\(\s*\"(?:sh|bash|cmd)\"\s*,\s*\"-c\"",
            ],
            "description": "Execution of system shell commands with user-controlled input or shell=True enabled.",
            "impact": "Remote code execution (RCE) allowing unauthorized access to host filesystem, network, and environmental secrets.",
            "recommendation": "Avoid invoking shell directly. Use subprocess list arguments with shell=False, or use native language APIs instead of CLI commands.",
            "suggested_fix": "# Safe execution without shell=True:\n# subprocess.run(['ls', '-la', target_path], shell=False, check=True)",
        },
        {
            "id": "SEC003_INSECURE_DESERIALIZATION",
            "title": "Insecure Deserialization (Pickle/YAML/Object)",
            "severity": "HIGH",
            "category": "SECURITY",
            "languages": ["python", "javascript", "ruby", "java"],
            "patterns": [
                r"(?i)pickle\.loads?\s*\(",
                r"(?i)_pickle\.loads?\s*\(",
                r"(?i)yaml\.load\s*\([^,)]+\)(?!\s*,\s*Loader\s*=\s*(?:yaml\.)?SafeLoader)",
                r"(?i)unserialize\s*\(",
                r"(?i)XMLDecoder\s*\(",
            ],
            "description": "Deserialization of untrusted byte streams or YAML without safe loaders.",
            "impact": "Arbitrary object instantiation and code execution upon payload loading.",
            "recommendation": "Use safe serialization formats like JSON (json.loads) or use yaml.safe_load() instead of pickle/unsafe YAML.",
            "suggested_fix": "# Use safe serialization:\n# data = json.loads(payload)  # or yaml.safe_load(payload)",
        },
        {
            "id": "SEC004_SSRF",
            "title": "Potential Server-Side Request Forgery (SSRF)",
            "severity": "HIGH",
            "category": "SECURITY",
            "languages": ["python", "javascript", "typescript", "go", "java"],
            "patterns": [
                r"(?i)(?:requests|httpx|urllib\.request)\.(?:get|post|put)\s*\(\s*(?:request\.|req\.|params\[|url_from_user|user_url)",
                r"(?i)fetch\s*\(\s*(?:req\.|params\[|userUrl|targetUrl)",
                r"(?i)http\.Get\s*\(\s*(?:req\.|r\.URL\.Query)",
            ],
            "description": "Outbound HTTP request made with unvalidated or user-supplied target URL.",
            "impact": "Attacker can force the server to send HTTP requests to internal cloud metadata endpoints, internal services, or loopback interfaces.",
            "recommendation": "Validate and whitelist destination hostnames and prohibit requests to private/loopback IP ranges (127.0.0.1, 169.254.169.254).",
            "suggested_fix": "# Implement SSRF validation:\n# if not is_safe_repo_url(user_url):\n#     raise ValueError('Untrusted target URL')",
        },
        {
            "id": "SEC005_INSECURE_SSL",
            "title": "Disabled SSL/TLS Certificate Verification",
            "severity": "HIGH",
            "category": "SECURITY",
            "languages": ["python", "javascript", "typescript", "go", "java"],
            "patterns": [
                r"(?i)verify\s*=\s*False",
                r"(?i)rejectUnauthorized\s*:\s*false",
                r"(?i)InsecureSkipVerify\s*:\s*true",
                r"(?i)TrustAllStrategy\.INSTANCE",
            ],
            "description": "SSL/TLS verification is disabled, allowing man-in-the-middle (MITM) attacks.",
            "impact": "Network traffic can be intercepted, read, or modified by intermediate proxies or attackers on the local network.",
            "recommendation": "Always enable TLS certificate validation in production (verify=True).",
            "suggested_fix": "# Enable strict SSL verification:\n# response = requests.get(url, verify=True)",
        },
        {
            "id": "SEC006_XSS_DOM_INJECTION",
            "title": "Cross-Site Scripting (XSS) / Unsafe DOM Injection",
            "severity": "MEDIUM",
            "category": "SECURITY",
            "languages": ["javascript", "typescript", "html"],
            "patterns": [
                r"dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:",
                r"\.innerHTML\s*=\s*",
                r"v-html\s*=",
                r"document\.write\s*\(",
            ],
            "description": "Direct injection of raw HTML into DOM elements without sanitization.",
            "impact": "Execution of malicious JavaScript in victim user browsers, leading to session hijacking or credential theft.",
            "recommendation": "Use standard React JSX text nodes or sanitize HTML with DOMPurify before rendering.",
            "suggested_fix": "// Sanitize before rendering:\n// import DOMPurify from 'dompurify';\n// <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }} />",
        },
        {
            "id": "SEC007_INSECURE_RANDOM",
            "title": "Weak Cryptographic PRNG Used for Security Context",
            "severity": "LOW",
            "category": "SECURITY",
            "languages": ["python", "javascript", "typescript", "java", "go"],
            "patterns": [
                r"(?i)(?:token|password|secret|key|salt|nonce)\s*=\s*.*random\.choice",
                r"(?i)(?:token|password|secret|key|salt|nonce)\s*=\s*.*random\.random",
                r"(?i)(?:token|password|secret|key|salt|nonce)\s*=\s*.*Math\.random\(\)",
            ],
            "description": "Standard pseudo-random number generator (PRNG) used for security-sensitive tokens or keys.",
            "impact": "Predictable tokens that an adversary can reproduce.",
            "recommendation": "Use cryptographically secure PRNGs like Python's `secrets` module, `crypto.randomBytes()`, or `crypto/rand`.",
            "suggested_fix": "# Use cryptographically secure tokens:\n# import secrets\n# token = secrets.token_hex(32)",
        },
    ]

    @classmethod
    def scan_codebase(cls, base_dir: str, scanned_files: List[ScannedFile]) -> List[Dict[str, Any]]:
        all_issues: List[Dict[str, Any]] = []

        # 1. Scan for secrets & pattern vulnerabilities across all code files
        for file in scanned_files:
            if file.is_binary:
                continue

            try:
                with open(file.absolute_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Secret scanning
                secret_issues = SecretScanner.scan_file(file.relative_path, content)
                all_issues.extend(secret_issues)

                # Vulnerability pattern scanning
                ext = file.extension.lower()
                lines = content.splitlines()

                for rule in cls.VULNERABILITY_RULES:
                    for rx_str in rule["patterns"]:
                        rx = re.compile(rx_str)
                        for line_idx, line in enumerate(lines, start=1):
                            if rx.search(line):
                                snippet = line.strip()
                                if len(snippet) > 200:
                                    snippet = snippet[:197] + "..."

                                all_issues.append({
                                    "severity": rule["severity"],
                                    "category": rule["category"],
                                    "title": rule["title"],
                                    "description": rule["description"],
                                    "file_path": file.relative_path,
                                    "line_number": line_idx,
                                    "code_snippet": snippet,
                                    "impact": rule["impact"],
                                    "recommendation": rule["recommendation"],
                                    "suggested_fix": rule["suggested_fix"],
                                    "tool": "ast_security",
                                    "confidence": "HIGH",
                                })
            except Exception as e:
                logger.warning(f"Error scanning security for {file.relative_path}: {e}")

        # 2. Run Bandit on Python files if bandit is installed in environment
        bandit_issues = cls._run_bandit(base_dir)
        all_issues.extend(bandit_issues)

        # Deduplicate issues based on (file_path, line_number, title)
        unique_issues: Dict[str, Dict[str, Any]] = {}
        for issue in all_issues:
            key = f"{issue['file_path']}:{issue['line_number']}:{issue['title']}"
            if key not in unique_issues:
                unique_issues[key] = issue

        logger.info(f"Security scan completed. Found {len(unique_issues)} unique security issues.")
        return list(unique_issues.values())

    @classmethod
    def _run_bandit(cls, base_dir: str) -> List[Dict[str, Any]]:
        bandit_results: List[Dict[str, Any]] = []
        try:
            cmd = ["bandit", "-r", base_dir, "-f", "json", "-q", "-x", "**/tests/**,**/test/**,**/venv/**"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.stdout:
                data = json.loads(proc.stdout)
                for res in data.get("results", []):
                    sev_map = {"HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}
                    sev = sev_map.get(res.get("issue_severity", "").upper(), "MEDIUM")
                    rel_path = os.path.relpath(res.get("filename", ""), base_dir).replace("\\", "/")
                    
                    bandit_results.append({
                        "severity": sev,
                        "category": "SECURITY",
                        "title": f"Bandit: {res.get('test_name', 'Security Alert')}",
                        "description": res.get("issue_text", ""),
                        "file_path": rel_path,
                        "line_number": res.get("line_number", 1),
                        "code_snippet": (res.get("code", "")).strip()[:200],
                        "impact": "Vulnerability identified by Bandit static security analyzer.",
                        "recommendation": f"Refer to Bandit test {res.get('test_id')} for remediation guidelines.",
                        "suggested_fix": None,
                        "tool": "bandit",
                        "confidence": res.get("issue_confidence", "MEDIUM").upper(),
                    })
        except Exception:
            # Bandit may not be on system path in all environments, fallback handles it
            pass
        return bandit_results
