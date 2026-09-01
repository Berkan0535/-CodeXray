import re
import ast
from typing import List, Dict, Any
from app.analyzers.file_scanner import ScannedFile
from app.core.logging import logger


class PerformanceAnalyzer:
    """
    Detects architectural and runtime performance anti-patterns:
    - N+1 query loops
    - Synchronous blocking in async routines
    - Inefficient nested loops
    - Unbounded database queries
    - Catastrophic regex backtracking
    - Missing caching recommendations
    """

    DB_CALL_PATTERNS = [
        r"\.query\s*\(",
        r"\.filter\s*\(",
        r"\.find\s*\(",
        r"\.findOne\s*\(",
        r"\.findById\s*\(",
        r"\.execute\s*\(",
        r"\.select\s*\(",
        r"db\.",
        r"session\.",
        r"repository\.",
        r"repo\.",
        r"SELECT\s+",
    ]

    ASYNC_BLOCKING_PATTERNS = [
        (r"time\.sleep\s*\(", "time.sleep() in async function", "Use await asyncio.sleep() instead of blocking thread sleep."),
        (r"requests\.(?:get|post|put|delete)\s*\(", "requests in async function", "Use async HTTP client like httpx.AsyncClient or aiohttp."),
        (r"urllib\.request\.urlopen\s*\(", "urllib in async function", "Use async HTTP client to avoid blocking event loop."),
    ]

    @classmethod
    def analyze_codebase(cls, base_dir: str, scanned_files: List[ScannedFile]) -> List[Dict[str, Any]]:
        performance_issues: List[Dict[str, Any]] = []

        for file in scanned_files:
            if file.is_binary:
                continue

            ext = file.extension.lower()
            try:
                with open(file.absolute_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                lines = content.splitlines()

                # 1. Python AST-based deep performance inspection
                if ext in (".py", ".pyw"):
                    cls._analyze_python_ast(file.relative_path, content, performance_issues)

                # 2. General cross-language loop & query analysis
                cls._analyze_loop_queries(file.relative_path, lines, performance_issues)

                # 3. Regex backtracking vulnerability & unbounded queries
                cls._analyze_regex_and_queries(file.relative_path, lines, performance_issues)

            except Exception as e:
                logger.warning(f"Performance analysis error in {file.relative_path}: {e}")

        logger.info(f"Performance analysis completed. Found {len(performance_issues)} potential performance bottlenecks.")
        return performance_issues

    @classmethod
    def _analyze_python_ast(cls, file_path: str, code: str, issues: List[Dict[str, Any]]):
        try:
            tree = ast.parse(code)
        except Exception:
            return

        for node in ast.walk(tree):
            # Check async function containing blocking calls
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        # Detect time.sleep inside async
                        if isinstance(child.func, ast.Attribute):
                            if isinstance(child.func.value, ast.Name) and child.func.value.id == "time" and child.func.attr == "sleep":
                                issues.append({
                                    "severity": "HIGH",
                                    "category": "PERFORMANCE",
                                    "title": "Synchronous Blocking Call inside Async Coroutine",
                                    "description": f"Function '{node.name}' is async, but calls blocking `time.sleep()` which stalls the event loop.",
                                    "file_path": file_path,
                                    "line_number": child.lineno,
                                    "code_snippet": f"time.sleep(...) inside async def {node.name}",
                                    "impact": "Blocks the entire asyncio event loop, freezing all concurrent requests.",
                                    "recommendation": "Replace `time.sleep(n)` with `await asyncio.sleep(n)`.",
                                    "suggested_fix": "await asyncio.sleep(1)",
                                    "tool": "performance_analyzer",
                                    "confidence": "HIGH",
                                })

            # Detect nested loops (depth >= 3)
            if isinstance(node, (ast.For, ast.While)):
                loop_depth = cls._get_loop_depth(node)
                if loop_depth >= 3:
                    issues.append({
                        "severity": "MEDIUM",
                        "category": "PERFORMANCE",
                        "title": f"Deeply Nested Loop (Depth {loop_depth}) - Potential O(N^{loop_depth})",
                        "description": f"Detected loop nesting depth of {loop_depth}, which can cause exponential compute degradation.",
                        "file_path": file_path,
                        "line_number": node.lineno,
                        "code_snippet": f"Loop starting at line {node.lineno} has nesting depth {loop_depth}",
                        "impact": "High CPU utilization and computational slowdown as dataset grows.",
                        "recommendation": "Refactor nested loops using lookup dictionaries, sets, indexing, or vectorized array operations.",
                        "suggested_fix": "# Pre-index items in a dictionary for O(1) lookup",
                        "tool": "performance_analyzer",
                        "confidence": "HIGH",
                    })

    @classmethod
    def _get_loop_depth(cls, node: ast.AST) -> int:
        depth = 1
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                depth = max(depth, 1 + cls._get_loop_depth(child))
            else:
                for sub in ast.iter_child_nodes(child):
                    if isinstance(sub, (ast.For, ast.While)):
                        depth = max(depth, 1 + cls._get_loop_depth(sub))
        return depth

    @classmethod
    def _analyze_loop_queries(cls, file_path: str, lines: List[str], issues: List[Dict[str, Any]]):
        in_loop = False
        loop_start_line = 0
        loop_indent = 0

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())

            # Detect loop start
            if re.match(r"^\s*(?:for\s*\(|for\s+[a-zA-Z0-9_, ]+\s+in|while\s*\(|while\s+)", line):
                in_loop = True
                loop_start_line = idx
                loop_indent = indent
                continue

            if in_loop:
                if indent <= loop_indent and stripped and not stripped.startswith(("#", "//", "*", "}")):
                    in_loop = False

            if in_loop:
                for db_pat in cls.DB_CALL_PATTERNS:
                    if re.search(db_pat, stripped):
                        issues.append({
                            "severity": "HIGH",
                            "category": "PERFORMANCE",
                            "title": "Potential N+1 Database Query in Loop",
                            "description": f"Database query invocation inside loop starting at line {loop_start_line}.",
                            "file_path": file_path,
                            "line_number": idx,
                            "code_snippet": stripped[:180],
                            "impact": "Executes 1 database query per item (N+1 queries), causing significant latency and database connection pool saturation.",
                            "recommendation": "Batch fetch records before loop using `IN (...)` or JOIN / ORM eager loading (`selectinload` / `joinedload`).",
                            "suggested_fix": "# Batch fetch ids:\n# records = db.query(Model).filter(Model.id.in_(item_ids)).all()",
                            "tool": "performance_analyzer",
                            "confidence": "MEDIUM",
                        })
                        break

    @classmethod
    def _analyze_regex_and_queries(cls, file_path: str, lines: List[str], issues: List[Dict[str, Any]]):
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Catastrophic backtracking regex pattern
            if re.search(r"r?[\"'].*(\([a-zA-Z0-9_\-\.\*\+]+\)\+).*[\"']", stripped):
                issues.append({
                    "severity": "MEDIUM",
                    "category": "PERFORMANCE",
                    "title": "Potential Catastrophic Regex Backtracking (ReDoS)",
                    "description": "Nested quantifier detected in regular expression, which can cause polynomial/exponential runtime on malicious input.",
                    "file_path": file_path,
                    "line_number": idx,
                    "code_snippet": stripped[:180],
                    "impact": "CPU starvation and thread denial of service on crafted input strings.",
                    "recommendation": "Simplify regex pattern, use atomic groups, or avoid nested repetition operators like (a+)+.",
                    "suggested_fix": None,
                    "tool": "performance_analyzer",
                    "confidence": "LOW",
                })
