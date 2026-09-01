import ast
import re
from typing import List, Dict, Any, Optional
from app.core.logging import logger

try:
    import tree_sitter
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_java
    import tree_sitter_go
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


class ASTSymbol:
    def __init__(
        self,
        name: str,
        kind: str,  # function, class, method, interface, import
        file_path: str,
        start_line: int,
        end_line: int,
        docstring: Optional[str] = None,
        complexity: int = 1,
        params: Optional[List[str]] = None,
        parent: Optional[str] = None,
        is_async: bool = False,
    ):
        self.name = name
        self.kind = kind
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.docstring = docstring
        self.complexity = complexity
        self.params = params or []
        self.parent = parent
        self.is_async = is_async

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "docstring": self.docstring,
            "complexity": self.complexity,
            "params": self.params,
            "parent": self.parent,
            "is_async": self.is_async,
        }


class ASTImport:
    def __init__(self, module: str, symbols: List[str], line_number: int, is_relative: bool = False):
        self.module = module
        self.symbols = symbols
        self.line_number = line_number
        self.is_relative = is_relative

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "symbols": self.symbols,
            "line_number": self.line_number,
            "is_relative": self.is_relative,
        }


class ParsedFileAST:
    def __init__(self, file_path: str, language: str):
        self.file_path = file_path
        self.language = language
        self.symbols: List[ASTSymbol] = []
        self.imports: List[ASTImport] = []
        self.call_sites: List[Dict[str, Any]] = []
        self.total_complexity: int = 0
        self.parse_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": [i.to_dict() for i in self.imports],
            "call_sites": self.call_sites,
            "total_complexity": self.total_complexity,
            "parse_error": self.parse_error,
        }


class TreeSitterParserEngine:
    """
    Unified multi-language AST parser with Tree-Sitter and Python AST fallback.
    Supports Python, JavaScript, TypeScript, Java, and Go.
    """

    def __init__(self):
        self._parsers: Dict[str, Any] = {}
        if HAS_TREE_SITTER:
            self._init_tree_sitter_parsers()

    def _init_tree_sitter_parsers(self):
        try:
            # Python
            py_lang = tree_sitter.Language(tree_sitter_python.language())
            self._parsers["python"] = tree_sitter.Parser(py_lang)
            
            # JavaScript
            js_lang = tree_sitter.Language(tree_sitter_javascript.language())
            self._parsers["javascript"] = tree_sitter.Parser(js_lang)
            
            # TypeScript
            ts_lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())
            self._parsers["typescript"] = tree_sitter.Parser(ts_lang)
            
            # Java
            java_lang = tree_sitter.Language(tree_sitter_java.language())
            self._parsers["java"] = tree_sitter.Parser(java_lang)
            
            # Go
            go_lang = tree_sitter.Language(tree_sitter_go.language())
            self._parsers["go"] = tree_sitter.Parser(go_lang)
        except Exception as e:
            logger.warning(f"Tree-sitter parser initialization note: {e}")

    def parse_file(self, file_path: str, code: str, language: str) -> ParsedFileAST:
        lang_lower = language.lower()
        result = ParsedFileAST(file_path=file_path, language=language)

        if lang_lower == "python":
            return self._parse_python(file_path, code, result)
        elif lang_lower in ("javascript", "typescript") and HAS_TREE_SITTER:
            return self._parse_tree_sitter(file_path, code, lang_lower, result)
        elif lang_lower in ("java", "go") and HAS_TREE_SITTER:
            return self._parse_tree_sitter(file_path, code, lang_lower, result)
        else:
            return self._regex_fallback_parse(file_path, code, language, result)

    def _parse_python(self, file_path: str, code: str, result: ParsedFileAST) -> ParsedFileAST:
        """Parses Python using python's built-in robust AST."""
        try:
            tree = ast.parse(code, filename=file_path)
        except SyntaxError as e:
            result.parse_error = f"Syntax error at line {e.lineno}: {e.msg}"
            return result
        except Exception as e:
            result.parse_error = str(e)
            return result

        class PythonASTVisitor(ast.NodeVisitor):
            def __init__(self, res: ParsedFileAST):
                self.res = res
                self.current_class = None

            def visit_Import(self, node: ast.Import):
                for alias in node.names:
                    self.res.imports.append(
                        ASTImport(module=alias.name, symbols=[alias.asname or alias.name], line_number=node.lineno)
                    )
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom):
                mod = node.module or ""
                symbols = [a.name for a in node.names]
                self.res.imports.append(
                    ASTImport(module=mod, symbols=symbols, line_number=node.lineno, is_relative=node.level > 0)
                )
                self.generic_visit(node)

            def visit_ClassDef(self, node: ast.ClassDef):
                doc = ast.get_docstring(node)
                self.res.symbols.append(
                    ASTSymbol(
                        name=node.name,
                        kind="class",
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        docstring=doc,
                        complexity=1,
                    )
                )
                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._handle_func(node, is_async=False)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._handle_func(node, is_async=True)

            def _handle_func(self, node, is_async: bool):
                doc = ast.get_docstring(node)
                params = [a.arg for a in node.args.args]
                
                # Calculate function cyclomatic complexity
                complexity = 1
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert)):
                        complexity += 1
                    elif isinstance(sub, ast.BoolOp):
                        complexity += len(sub.values) - 1

                self.res.total_complexity += complexity
                self.res.symbols.append(
                    ASTSymbol(
                        name=node.name,
                        kind="method" if self.current_class else "function",
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        docstring=doc,
                        complexity=complexity,
                        params=params,
                        parent=self.current_class,
                        is_async=is_async,
                    )
                )
                self.generic_visit(node)

            def visit_Call(self, node: ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name:
                    self.res.call_sites.append({
                        "name": func_name,
                        "line": node.lineno,
                    })
                self.generic_visit(node)

        visitor = PythonASTVisitor(result)
        visitor.visit(tree)
        return result

    def _parse_tree_sitter(self, file_path: str, code: str, lang: str, result: ParsedFileAST) -> ParsedFileAST:
        parser = self._parsers.get(lang)
        if not parser:
            return self._regex_fallback_parse(file_path, code, lang, result)

        try:
            tree = parser.parse(bytes(code, "utf8"))
            root_node = tree.root_node
            
            def traverse(node, current_class=None):
                node_type = node.type
                
                # Functions & Methods
                if node_type in (
                    "function_declaration", "method_definition", "arrow_function",
                    "function_item", "method_declaration", "function_declaration_statement"
                ):
                    name = "anonymous"
                    # Find identifier child
                    for child in node.children:
                        if child.type in ("identifier", "property_identifier", "name"):
                            name = code[child.start_byte:child.end_byte]
                            break

                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    
                    # Cyclomatic complexity estimate from branching nodes (recursive traversal of function body)
                    def count_branching(sub_node):
                        c = 0
                        if sub_node.type in (
                            "if_statement", "for_statement", "for_in_statement",
                            "while_statement", "catch_clause", "switch_case", "ternary_expression",
                            "binary_expression", "logical_and", "logical_or"
                        ):
                            c += 1
                        for child_sub in sub_node.children:
                            c += count_branching(child_sub)
                        return c

                    complexity = 1 + count_branching(node)

                    result.total_complexity += complexity
                    result.symbols.append(
                        ASTSymbol(
                            name=name,
                            kind="method" if current_class else "function",
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            complexity=complexity,
                            parent=current_class,
                        )
                    )
                
                # Classes & Interfaces
                elif node_type in ("class_declaration", "class", "interface_declaration", "struct_spec", "type_spec"):
                    class_name = "AnonymousClass"
                    for child in node.children:
                        if child.type in ("identifier", "type_identifier", "name"):
                            class_name = code[child.start_byte:child.end_byte]
                            break

                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    result.symbols.append(
                        ASTSymbol(
                            name=class_name,
                            kind="class",
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                        )
                    )
                    current_class = class_name

                # Imports
                elif node_type in ("import_statement", "import_declaration", "require_call"):
                    raw_import = code[node.start_byte:node.end_byte]
                    result.imports.append(
                        ASTImport(
                            module=raw_import[:100],
                            symbols=[],
                            line_number=node.start_point[0] + 1
                        )
                    )

                for child in node.children:
                    traverse(child, current_class)

            traverse(root_node)
            return result
        except Exception as e:
            logger.warning(f"Tree-sitter parsing error for {file_path}: {e}")
            return self._regex_fallback_parse(file_path, code, lang, result)

    def _regex_fallback_parse(self, file_path: str, code: str, language: str, result: ParsedFileAST) -> ParsedFileAST:
        """Regex heuristics fallback for any arbitrary language."""
        lines = code.splitlines()
        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            # Detect functions: e.g. func Name, def Name, function Name
            func_match = re.match(r"(?:public|private|protected|static|async|def|func|function|fn)\s+([A-Za-z0-9_]+)\s*\(", line_str)
            if func_match:
                result.symbols.append(
                    ASTSymbol(
                        name=func_match.group(1),
                        kind="function",
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx + 10,
                        complexity=1
                    )
                )
                result.total_complexity += 1

            # Detect imports
            if line_str.startswith(("import ", "from ", "require(", "include ")):
                result.imports.append(
                    ASTImport(module=line_str[:120], symbols=[], line_number=idx)
                )

            # Detect classes
            class_match = re.match(r"(?:class|interface|struct|type)\s+([A-Za-z0-9_]+)", line_str)
            if class_match:
                result.symbols.append(
                    ASTSymbol(
                        name=class_match.group(1),
                        kind="class",
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx + 20
                    )
                )

        return result
