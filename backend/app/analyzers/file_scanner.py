import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


IGNORE_DIRS = {
    ".git",
    ".github",
    ".gitlab",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    "dist",
    "build",
    "out",
    ".next",
    ".nuxt",
    ".turbo",
    "coverage",
    ".nyc_output",
    ".idea",
    ".vscode",
    "target",
    "bin",
    "obj",
    ".tox",
    "vendor",
    "bower_components",
    ".serverless",
    ".terraform",
    ".gradle",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp", ".tiff",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".pyd", ".class", ".o", ".a",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".flac",
    ".sqlite", ".db", ".sqlite3",
    ".wasm", ".lockb",
}


class ScannedFile:
    def __init__(
        self,
        relative_path: str,
        absolute_path: str,
        size_bytes: int,
        total_lines: int = 0,
        code_lines: int = 0,
        comment_lines: int = 0,
        blank_lines: int = 0,
        is_binary: bool = False,
        extension: str = ""
    ):
        self.relative_path = relative_path
        self.absolute_path = absolute_path
        self.size_bytes = size_bytes
        self.total_lines = total_lines
        self.code_lines = code_lines
        self.comment_lines = comment_lines
        self.blank_lines = blank_lines
        self.is_binary = is_binary
        self.extension = extension

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "is_binary": self.is_binary,
            "extension": self.extension,
        }


class FileScanner:
    """
    High-performance, resource-safe repository scanner.
    Excludes unwanted directories, binaries, and oversized files.
    """

    @classmethod
    def is_binary_file(cls, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        if ext in BINARY_EXTENSIONS:
            return True
        try:
            with open(filepath, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:
                    return True
        except Exception:
            return True
        return False

    @classmethod
    def count_lines(cls, filepath: str) -> tuple[int, int, int, int]:
        """
        Calculates (total_lines, code_lines, comment_lines, blank_lines)
        """
        total = 0
        blank = 0
        comment = 0
        code = 0
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    total += 1
                    s = line.strip()
                    if not s:
                        blank += 1
                    elif s.startswith(("#", "//", "/*", "*", "<!--", "--", ";")):
                        comment += 1
                    else:
                        code += 1
        except Exception:
            pass
            
        return total, code, comment, blank

    @classmethod
    def scan_directory(cls, base_dir: str) -> List[ScannedFile]:
        """
        Walks the directory tree, respecting limits and ignore rules.
        """
        scanned_files: List[ScannedFile] = []
        base_path = Path(base_dir).resolve()
        max_file_size = settings.MAX_FILE_SIZE_KB * 1024
        
        for root, dirs, files in os.walk(base_path):
            # Modify dirs in-place to prevent entering ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            
            for file in files:
                if len(scanned_files) >= settings.MAX_ANALYSIS_FILES:
                    logger.warning(f"Hit max file limit ({settings.MAX_ANALYSIS_FILES}). Stopping scan.")
                    break
                    
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")
                
                # Check extension and size
                ext = os.path.splitext(file)[1].lower()
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    continue

                if size > max_file_size or cls.is_binary_file(full_path):
                    scanned_files.append(
                        ScannedFile(
                            relative_path=rel_path,
                            absolute_path=full_path,
                            size_bytes=size,
                            is_binary=True,
                            extension=ext
                        )
                    )
                    continue

                total, code, comment, blank = cls.count_lines(full_path)
                scanned_files.append(
                    ScannedFile(
                        relative_path=rel_path,
                        absolute_path=full_path,
                        size_bytes=size,
                        total_lines=total,
                        code_lines=code,
                        comment_lines=comment,
                        blank_lines=blank,
                        is_binary=False,
                        extension=ext
                    )
                )

        logger.info(f"Scanned {len(scanned_files)} files in {base_dir}")
        return scanned_files
