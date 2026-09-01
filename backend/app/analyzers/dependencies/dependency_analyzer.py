import os
import json
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
from app.analyzers.file_scanner import ScannedFile
from app.core.logging import logger


KNOWN_VULNERABILITIES: Dict[str, List[Dict[str, Any]]] = {
    "lodash": [
        {"vulnerable_below": "4.17.21", "cve": "CVE-2021-23337", "severity": "HIGH", "desc": "Command Injection in template"},
        {"vulnerable_below": "4.17.20", "cve": "CVE-2020-8203", "severity": "HIGH", "desc": "Prototype Pollution"},
    ],
    "axios": [
        {"vulnerable_below": "1.7.4", "cve": "CVE-2024-39338", "severity": "MEDIUM", "desc": "SSRF vulnerability in baseURL"},
    ],
    "jsonwebtoken": [
        {"vulnerable_below": "9.0.0", "cve": "CVE-2022-23529", "severity": "CRITICAL", "desc": "Insecure Key Retrieval and verification bypass"},
    ],
    "express": [
        {"vulnerable_below": "4.19.2", "cve": "CVE-2024-29041", "severity": "HIGH", "desc": "Open redirect in express response"},
    ],
    "requests": [
        {"vulnerable_below": "2.31.0", "cve": "CVE-2023-32681", "severity": "MEDIUM", "desc": "Unintended leak of Proxy-Authorization header"},
    ],
    "urllib3": [
        {"vulnerable_below": "1.26.18", "cve": "CVE-2023-45803", "severity": "MEDIUM", "desc": "Cookie leak across redirects"},
        {"vulnerable_below": "2.0.7", "cve": "CVE-2023-45803", "severity": "MEDIUM", "desc": "Cookie leak across redirects"},
    ],
    "cryptography": [
        {"vulnerable_below": "41.0.6", "cve": "CVE-2023-49083", "severity": "HIGH", "desc": "NULL-dereference when loading PKCS#7 certificates"},
    ],
    "log4j-core": [
        {"vulnerable_below": "2.17.1", "cve": "CVE-2021-44228", "severity": "CRITICAL", "desc": "Log4Shell JNDI Remote Code Execution"},
    ],
    "fastjson": [
        {"vulnerable_below": "1.2.83", "cve": "CVE-2022-25845", "severity": "CRITICAL", "desc": "AutoType bypass deserialization RCE"},
    ],
}


class DependencyAnalyzer:
    """
    Parses manifest files (package.json, requirements.txt, pyproject.toml, go.mod, pom.xml, Cargo.toml),
    extracts ecosystem packages, and inspects vulnerability status.
    """

    @classmethod
    def analyze(cls, base_dir: str, scanned_files: List[ScannedFile]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        dependencies: List[Dict[str, Any]] = []
        dep_issues: List[Dict[str, Any]] = []

        file_map = {f.relative_path: f for f in scanned_files}

        for rel_path, file in file_map.items():
            base_name = os.path.basename(rel_path).lower()

            try:
                # 1. package.json (npm)
                if base_name == "package.json":
                    cls._parse_package_json(file.absolute_path, rel_path, dependencies, dep_issues)

                # 2. requirements.txt (pypi)
                elif base_name == "requirements.txt" or (base_name.endswith(".txt") and "req" in base_name):
                    cls._parse_requirements_txt(file.absolute_path, rel_path, dependencies, dep_issues)

                # 3. pyproject.toml (pypi/poetry)
                elif base_name == "pyproject.toml":
                    cls._parse_pyproject_toml(file.absolute_path, rel_path, dependencies, dep_issues)

                # 4. go.mod (golang)
                elif base_name == "go.mod":
                    cls._parse_go_mod(file.absolute_path, rel_path, dependencies, dep_issues)

                # 5. pom.xml (maven)
                elif base_name == "pom.xml":
                    cls._parse_pom_xml(file.absolute_path, rel_path, dependencies, dep_issues)

                # 6. Cargo.toml (rust)
                elif base_name == "cargo.toml":
                    cls._parse_cargo_toml(file.absolute_path, rel_path, dependencies, dep_issues)

            except Exception as e:
                logger.warning(f"Error parsing manifest {rel_path}: {e}")

        logger.info(f"Dependency analysis completed. Found {len(dependencies)} dependencies.")
        return dependencies, dep_issues

    @classmethod
    def _parse_package_json(cls, full_path: str, rel_path: str, deps: List[Dict[str, Any]], issues: List[Dict[str, Any]]):
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)

        merged = {}
        merged.update(data.get("dependencies", {}))
        merged.update(data.get("devDependencies", {}))

        for name, ver in merged.items():
            clean_ver = str(ver).lstrip("^~>=< ")
            vulns = cls._check_vulnerabilities(name, clean_ver)
            is_outdated = ver in ("*", "latest") or "^" in str(ver)

            dep_entry = {
                "name": name,
                "version": str(ver),
                "ecosystem": "npm",
                "manifest_file": rel_path,
                "is_outdated": is_outdated,
                "latest_version": None,
                "vulnerabilities_count": len(vulns),
                "vulnerabilities": vulns,
            }
            deps.append(dep_entry)

            for v in vulns:
                issues.append({
                    "severity": v["severity"],
                    "category": "DEPENDENCY",
                    "title": f"Vulnerable Dependency: {name}@{ver} ({v['cve']})",
                    "description": f"Package '{name}' is vulnerable to {v['desc']}.",
                    "file_path": rel_path,
                    "line_number": 1,
                    "code_snippet": f'"{name}": "{ver}"',
                    "impact": f"Known CVE security vulnerability ({v['cve']}).",
                    "recommendation": f"Upgrade '{name}' to version {v['vulnerable_below']} or higher.",
                    "suggested_fix": f'"{name}": "^{v["vulnerable_below"]}"',
                    "tool": "dependency_analyzer",
                    "confidence": "HIGH",
                })

    @classmethod
    def _parse_requirements_txt(cls, full_path: str, rel_path: str, deps: List[Dict[str, Any]], issues: List[Dict[str, Any]]):
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, start=1):
                clean = line.strip()
                if not clean or clean.startswith(("#", "-", "git+")):
                    continue

                parts = re.split(r"(==|>=|<=|~=|>|<)", clean)
                name = parts[0].strip()
                version = "".join(parts[1:]).strip() if len(parts) > 1 else "unpinned"

                clean_ver = re.sub(r"[^\d.]", "", version) or "0.0.0"
                vulns = cls._check_vulnerabilities(name, clean_ver)

                deps.append({
                    "name": name,
                    "version": version or "latest",
                    "ecosystem": "pypi",
                    "manifest_file": rel_path,
                    "is_outdated": version == "unpinned",
                    "latest_version": None,
                    "vulnerabilities_count": len(vulns),
                    "vulnerabilities": vulns,
                })

                for v in vulns:
                    issues.append({
                        "severity": v["severity"],
                        "category": "DEPENDENCY",
                        "title": f"Vulnerable Python Dependency: {name}=={version} ({v['cve']})",
                        "description": f"Package '{name}' has known security advisory: {v['desc']}.",
                        "file_path": rel_path,
                        "line_number": idx,
                        "code_snippet": clean,
                        "impact": f"Vulnerability {v['cve']}.",
                        "recommendation": f"Upgrade {name} to version >={v['vulnerable_below']}.",
                        "suggested_fix": f"{name}>={v['vulnerable_below']}",
                        "tool": "dependency_analyzer",
                        "confidence": "HIGH",
                    })

    @classmethod
    def _parse_pyproject_toml(cls, full_path: str, rel_path: str, deps: List[Dict[str, Any]], issues: List[Dict[str, Any]]):
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        in_deps_block = False
        for idx, line in enumerate(content.splitlines(), start=1):
            if "[tool.poetry.dependencies]" in line or "dependencies = [" in line:
                in_deps_block = True
                continue
            if in_deps_block and line.startswith("["):
                in_deps_block = False

            if in_deps_block:
                m = re.match(r"^\s*([a-zA-Z0-9_\-]+)\s*=\s*[\"']([^\"']+)[\"']", line)
                if m:
                    name, ver = m.group(1), m.group(2)
                    if name.lower() != "python":
                        vulns = cls._check_vulnerabilities(name, ver.lstrip("^~>=< "))
                        deps.append({
                            "name": name,
                            "version": ver,
                            "ecosystem": "pypi",
                            "manifest_file": rel_path,
                            "is_outdated": False,
                            "latest_version": None,
                            "vulnerabilities_count": len(vulns),
                            "vulnerabilities": vulns,
                        })

    @classmethod
    def _parse_go_mod(cls, full_path: str, rel_path: str, deps: List[Dict[str, Any]], issues: List[Dict[str, Any]]):
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            in_require = False
            for line in f:
                stripped = line.strip()
                if stripped.startswith("require ("):
                    in_require = True
                    continue
                if in_require and stripped == ")":
                    in_require = False
                    continue
                if in_require or stripped.startswith("require "):
                    line_clean = stripped.replace("require ", "")
                    parts = line_clean.split()
                    if len(parts) >= 2:
                        deps.append({
                            "name": parts[0],
                            "version": parts[1],
                            "ecosystem": "golang",
                            "manifest_file": rel_path,
                            "is_outdated": False,
                            "latest_version": None,
                            "vulnerabilities_count": 0,
                            "vulnerabilities": [],
                        })

    @classmethod
    def _parse_pom_xml(cls, full_path: str, rel_path: str, deps: List[Dict[str, Any]], issues: List[Dict[str, Any]]):
        tree = ET.parse(full_path)
        root = tree.getroot()
        # strip namespaces
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        for dep in root.findall(".//dependency"):
            group = dep.findtext("groupId", "unknown")
            artifact = dep.findtext("artifactId", "unknown")
            version = dep.findtext("version", "latest")
            name = f"{group}:{artifact}"
            vulns = cls._check_vulnerabilities(artifact, version)

            deps.append({
                "name": name,
                "version": version,
                "ecosystem": "maven",
                "manifest_file": rel_path,
                "is_outdated": False,
                "latest_version": None,
                "vulnerabilities_count": len(vulns),
                "vulnerabilities": vulns,
            })

    @classmethod
    def _parse_cargo_toml(cls, full_path: str, rel_path: str, deps: List[Dict[str, Any]], issues: List[Dict[str, Any]]):
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            in_deps = False
            for line in f:
                stripped = line.strip()
                if stripped == "[dependencies]":
                    in_deps = True
                    continue
                if in_deps and stripped.startswith("["):
                    in_deps = False
                if in_deps and "=" in stripped:
                    parts = stripped.split("=", 1)
                    deps.append({
                        "name": parts[0].strip(),
                        "version": parts[1].strip().strip('"\''),
                        "ecosystem": "cargo",
                        "manifest_file": rel_path,
                        "is_outdated": False,
                        "latest_version": None,
                        "vulnerabilities_count": 0,
                        "vulnerabilities": [],
                    })

    @classmethod
    def _check_vulnerabilities(cls, name: str, version: str) -> List[Dict[str, Any]]:
        name_lower = name.lower()
        if name_lower not in KNOWN_VULNERABILITIES:
            return []

        matched = []
        for adv in KNOWN_VULNERABILITIES[name_lower]:
            # Simple version comparison check (e.g. if version starts with lower digit)
            target = adv["vulnerable_below"]
            if cls._is_version_less_than(version, target):
                matched.append(adv)
        return matched

    @staticmethod
    def _is_version_less_than(ver: str, target: str) -> bool:
        try:
            v_parts = [int(x) for x in re.findall(r"\d+", ver)[:3]]
            t_parts = [int(x) for x in re.findall(r"\d+", target)[:3]]
            while len(v_parts) < 3:
                v_parts.append(0)
            while len(t_parts) < 3:
                t_parts.append(0)
            return v_parts < t_parts
        except Exception:
            return False
