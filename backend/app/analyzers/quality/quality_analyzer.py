import hashlib
import math
from typing import List, Dict, Any, Tuple
from app.analyzers.file_scanner import ScannedFile
from app.analyzers.parser.ast_extractor import ParsedFileAST
from app.core.logging import logger


class QualityAnalyzer:
    """
    Evaluates codebase maintainability, cyclomatic complexity,
    duplication ratios, oversized units, and produces deterministic quality scores.
    """

    @classmethod
    def analyze(
        cls,
        scanned_files: List[ScannedFile],
        parsed_asts: List[ParsedFileAST]
    ) -> Dict[str, Any]:
        total_loc = 0
        total_code_lines = 0
        total_comment_lines = 0
        total_functions = 0
        total_classes = 0
        total_complexity = 0
        max_complexity = 0
        oversized_functions: List[Dict[str, Any]] = []
        oversized_files: List[Dict[str, Any]] = []
        quality_issues: List[Dict[str, Any]] = []

        # 1. Accumulate general lines
        for f in scanned_files:
            if f.is_binary:
                continue
            total_loc += f.total_lines
            total_code_lines += f.code_lines
            total_comment_lines += f.comment_lines

            if f.code_lines > 500:
                oversized_files.append({
                    "file_path": f.relative_path,
                    "code_lines": f.code_lines,
                    "total_lines": f.total_lines,
                })
                quality_issues.append({
                    "severity": "LOW",
                    "category": "QUALITY",
                    "title": f"Oversized File ({f.code_lines} lines)",
                    "description": f"File '{f.relative_path}' contains {f.code_lines} lines of code, violating Single Responsibility Principle (SRP).",
                    "file_path": f.relative_path,
                    "line_number": 1,
                    "code_snippet": None,
                    "impact": "Hard to navigate, test, and maintain.",
                    "recommendation": "Decompose into smaller focused modules or helper files.",
                    "suggested_fix": None,
                    "tool": "quality_analyzer",
                    "confidence": "HIGH",
                })

        # 2. Accumulate symbols & complexity from ASTs
        for ast_item in parsed_asts:
            total_complexity += ast_item.total_complexity
            for sym in ast_item.symbols:
                if sym.kind in ("function", "method"):
                    total_functions += 1
                    func_len = sym.end_line - sym.start_line + 1
                    if sym.complexity > max_complexity:
                        max_complexity = sym.complexity

                    if sym.complexity > 10 or func_len > 60:
                        oversized_functions.append({
                            "name": sym.name,
                            "file_path": sym.file_path,
                            "start_line": sym.start_line,
                            "lines": func_len,
                            "complexity": sym.complexity,
                        })
                        quality_issues.append({
                            "severity": "MEDIUM" if sym.complexity > 15 else "LOW",
                            "category": "QUALITY",
                            "title": f"High Cyclomatic Complexity in '{sym.name}' (CC={sym.complexity})",
                            "description": f"Function '{sym.name}' in {sym.file_path} has cyclomatic complexity of {sym.complexity} ({func_len} lines).",
                            "file_path": sym.file_path,
                            "line_number": sym.start_line,
                            "code_snippet": f"def/function {sym.name}(...)",
                            "impact": "Significantly higher defect rate, difficult to write complete unit tests.",
                            "recommendation": "Extract helper sub-functions to break down branching decision logic.",
                            "suggested_fix": None,
                            "tool": "quality_analyzer",
                            "confidence": "HIGH",
                        })
                elif sym.kind == "class":
                    total_classes += 1

        # 3. Detect code duplication across text files
        dup_percentage, dup_blocks = cls._detect_duplication(scanned_files)
        if dup_percentage > 10.0:
            quality_issues.append({
                "severity": "MEDIUM",
                "category": "QUALITY",
                "title": f"Code Duplication Rate at {dup_percentage:.1f}%",
                "description": f"Identified {len(dup_blocks)} duplicated blocks across multiple repository files.",
                "file_path": dup_blocks[0]["file_a"] if dup_blocks else "repository",
                "line_number": dup_blocks[0]["line_a"] if dup_blocks else 1,
                "code_snippet": None,
                "impact": "Code duplication requires changing multiple files for bug fixes, increasing regression risks.",
                "recommendation": "Extract common logic into shared utility functions or base classes (DRY principle).",
                "suggested_fix": None,
                "tool": "quality_analyzer",
                "confidence": "MEDIUM",
            })

        # 4. Compute deterministic metrics
        avg_complexity = (total_complexity / max(1, total_functions)) if total_functions > 0 else 1.0
        comment_ratio = round((total_comment_lines / max(1, total_code_lines + total_comment_lines) * 100), 2)

        # Maintainability Index (MI) estimation (normalized 0-100)
        # Standard formula: 171 - 5.2*ln(V) - 0.23*CC - 16.2*ln(LOC)
        loc_term = 16.2 * math.log(max(10, total_code_lines / max(1, len(scanned_files))))
        cc_term = 0.23 * avg_complexity
        raw_mi = 171.0 - loc_term - cc_term
        # Scale raw MI (typically 0-100)
        maintainability_index = max(10.0, min(100.0, raw_mi * (100.0 / 171.0) + (min(20.0, comment_ratio * 0.5))))

        # Sub-scores (0 - 100)
        complexity_score = max(20.0, min(100.0, 100.0 - (avg_complexity - 1.0) * 12.0))
        duplication_score = max(10.0, min(100.0, 100.0 - (dup_percentage * 2.5)))
        maintainability_score = round(maintainability_index, 1)
        code_quality_score = round((complexity_score * 0.35 + duplication_score * 0.35 + maintainability_score * 0.30), 1)

        return {
            "total_loc": total_loc,
            "total_code_lines": total_code_lines,
            "total_comment_lines": total_comment_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "avg_complexity": round(avg_complexity, 2),
            "max_complexity": max_complexity,
            "comment_ratio": comment_ratio,
            "duplication_percentage": round(dup_percentage, 1),
            "duplicated_blocks_count": len(dup_blocks),
            "maintainability_index": round(maintainability_index, 1),
            "scores": {
                "code_quality": code_quality_score,
                "maintainability": maintainability_score,
                "complexity": round(complexity_score, 1),
                "duplication": round(duplication_score, 1),
            },
            "oversized_functions": oversized_functions[:20],
            "oversized_files": oversized_files[:20],
            "quality_issues": quality_issues,
        }

    @classmethod
    def _detect_duplication(cls, scanned_files: List[ScannedFile]) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Sliding window block hash matcher for code duplication detection.
        """
        block_size = 6  # 6 lines threshold
        hashes: Dict[str, Tuple[str, int]] = {}
        dup_blocks: List[Dict[str, Any]] = []
        total_scanned_blocks = 0
        duplicated_blocks = 0

        # Sample code files up to 80 files
        text_files = [f for f in scanned_files if not f.is_binary and f.extension in (".py", ".js", ".ts", ".tsx", ".java", ".go")][:80]

        for f in text_files:
            try:
                with open(f.absolute_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    lines = [l.strip() for l in file_obj.readlines() if l.strip() and not l.strip().startswith(("#", "//", "/*", "*"))]

                if len(lines) < block_size:
                    continue

                for i in range(len(lines) - block_size + 1):
                    total_scanned_blocks += 1
                    block_text = "".join(lines[i : i + block_size])
                    block_hash = hashlib.md5(block_text.encode("utf-8")).hexdigest()

                    if block_hash in hashes:
                        orig_file, orig_line = hashes[block_hash]
                        if orig_file != f.relative_path:
                            duplicated_blocks += 1
                            if len(dup_blocks) < 15:
                                dup_blocks.append({
                                    "file_a": orig_file,
                                    "line_a": orig_line,
                                    "file_b": f.relative_path,
                                    "line_b": i + 1,
                                })
                    else:
                        hashes[block_hash] = (f.relative_path, i + 1)
            except Exception:
                continue

        dup_pct = (duplicated_blocks * 2.0 / max(1, total_scanned_blocks)) * 100.0 if total_scanned_blocks > 0 else 0.0
        return min(100.0, dup_pct), dup_blocks
