import os
from typing import List, Dict, Any, Optional
from app.analyzers.file_scanner import ScannedFile
from app.analyzers.parser.ast_extractor import ParsedFileAST, ASTSymbol


class CodeChunkItem:
    def __init__(
        self,
        file_path: str,
        symbol_name: Optional[str],
        chunk_type: str,  # function, class, block
        start_line: int,
        end_line: int,
        content: str,
    ):
        self.file_path = file_path
        self.symbol_name = symbol_name
        self.chunk_type = chunk_type
        self.start_line = start_line
        self.end_line = end_line
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
            "chunk_type": self.chunk_type,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
        }


class CodeChunker:
    """
    Splits codebase files into semantically meaningful chunks based on AST boundaries
    (functions, classes, methods) with sliding window fallback for other files.
    """

    @classmethod
    def chunk_repository(
        cls,
        base_dir: str,
        scanned_files: List[ScannedFile],
        parsed_asts: List[ParsedFileAST]
    ) -> List[CodeChunkItem]:
        chunks: List[CodeChunkItem] = []
        ast_map = {a.file_path: a for a in parsed_asts}

        for file in scanned_files:
            if file.is_binary:
                continue

            try:
                with open(file.absolute_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_content = f.read()

                lines = file_content.splitlines()
                ast_item = ast_map.get(file.relative_path)

                if ast_item and ast_item.symbols:
                    # 1. AST Symbol-based chunking
                    handled_lines = set()
                    for sym in ast_item.symbols:
                        s_line = max(1, sym.start_line)
                        e_line = min(len(lines), sym.end_line)
                        if s_line <= e_line:
                            chunk_lines = lines[s_line - 1 : e_line]
                            chunk_text = "\n".join(chunk_lines)
                            if len(chunk_text.strip()) > 20:
                                chunks.append(
                                    CodeChunkItem(
                                        file_path=file.relative_path,
                                        symbol_name=sym.name,
                                        chunk_type=sym.kind,
                                        start_line=s_line,
                                        end_line=e_line,
                                        content=chunk_text,
                                    )
                                )
                                for l in range(s_line, e_line + 1):
                                    handled_lines.add(l)

                    # If file has remaining unhandled top-level code (e.g. module level definitions)
                    if len(lines) > 0 and len(handled_lines) < len(lines) * 0.5:
                        cls._sliding_chunks(file.relative_path, lines, chunks)
                else:
                    # 2. Sliding window chunking for non-parsed or script files
                    cls._sliding_chunks(file.relative_path, lines, chunks)

            except Exception:
                continue

        return chunks

    @classmethod
    def _sliding_chunks(cls, file_path: str, lines: List[str], chunks: List[CodeChunkItem], chunk_size: int = 50, overlap: int = 10):
        if not lines:
            return

        step = max(1, chunk_size - overlap)
        for i in range(0, len(lines), step):
            chunk_lines = lines[i : i + chunk_size]
            chunk_text = "\n".join(chunk_lines)
            if len(chunk_text.strip()) > 15:
                chunks.append(
                    CodeChunkItem(
                        file_path=file_path,
                        symbol_name=None,
                        chunk_type="block",
                        start_line=i + 1,
                        end_line=min(len(lines), i + chunk_size),
                        content=chunk_text,
                    )
                )
