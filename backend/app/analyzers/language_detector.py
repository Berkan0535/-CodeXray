from typing import List, Dict, Any, Tuple
from app.analyzers.file_scanner import ScannedFile


EXTENSION_LANGUAGE_MAP: Dict[str, str] = {
    # Python
    ".py": "Python",
    ".pyi": "Python",
    ".pyw": "Python",
    # JavaScript & TypeScript
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    # Java & Kotlin
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    # Go
    ".go": "Go",
    # Rust
    ".rs": "Rust",
    # C & C++
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    # C#
    ".cs": "C#",
    # Ruby
    ".rb": "Ruby",
    # PHP
    ".php": "PHP",
    # Swift
    ".swift": "Swift",
    # Web & Styling
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    # Query & Config
    ".sql": "SQL",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
}


class LanguageDetector:
    """
    Identifies codebase programming languages, LOC distributions, and primary language.
    """

    @classmethod
    def detect_languages(cls, scanned_files: List[ScannedFile]) -> Dict[str, Any]:
        lang_stats: Dict[str, Dict[str, int]] = {}
        total_code_lines = 0
        total_files_count = 0

        for file in scanned_files:
            if file.is_binary:
                continue

            lang = EXTENSION_LANGUAGE_MAP.get(file.extension.lower(), "Other")
            if lang not in lang_stats:
                lang_stats[lang] = {"files": 0, "lines": 0, "code_lines": 0}

            lang_stats[lang]["files"] += 1
            lang_stats[lang]["lines"] += file.total_lines
            lang_stats[lang]["code_lines"] += file.code_lines

            total_code_lines += file.code_lines
            total_files_count += 1

        # Calculate percentages
        languages_breakdown: Dict[str, Dict[str, Any]] = {}
        for lang, stats in lang_stats.items():
            pct = round((stats["code_lines"] / total_code_lines * 100), 2) if total_code_lines > 0 else 0.0
            languages_breakdown[lang] = {
                "files": stats["files"],
                "lines": stats["lines"],
                "code_lines": stats["code_lines"],
                "percentage": pct,
            }

        # Filter and sort by code lines descending
        sorted_languages = sorted(
            languages_breakdown.items(),
            key=lambda x: x[1]["code_lines"],
            reverse=True
        )

        primary_language = sorted_languages[0][0] if sorted_languages else "Unknown"

        return {
            "primary_language": primary_language,
            "languages": dict(sorted_languages),
            "total_files": total_files_count,
            "total_code_lines": total_code_lines,
        }
