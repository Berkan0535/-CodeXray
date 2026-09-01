import pytest
from app.analyzers.parser.ast_extractor import TreeSitterParserEngine


def test_python_ast_parsing():
    engine = TreeSitterParserEngine()
    py_code = (
        "import os\n"
        "from typing import List\n\n"
        "class UserService:\n"
        "    '''Service managing users.'''\n"
        "    def __init__(self, db):\n"
        "        self.db = db\n\n"
        "    async def find_user(self, user_id: str):\n"
        "        if not user_id:\n"
        "            return None\n"
        "        return self.db.get(user_id)\n"
    )
    result = engine.parse_file("service.py", py_code, "python")
    assert result.parse_error is None
    assert len(result.symbols) >= 3  # Class + __init__ + find_user
    assert len(result.imports) >= 2

    class_sym = next(s for s in result.symbols if s.kind == "class")
    assert class_sym.name == "UserService"
    assert class_sym.docstring == "Service managing users."

    func_sym = next(s for s in result.symbols if s.name == "find_user")
    assert func_sym.is_async is True
    assert func_sym.complexity >= 2  # Has `if` statement


def test_javascript_ast_parsing():
    engine = TreeSitterParserEngine()
    js_code = (
        "function calculateTotal(items) {\n"
        "  let sum = 0;\n"
        "  for (let i = 0; i < items.length; i++) {\n"
        "    if (items[i].active) {\n"
        "      sum += items[i].price;\n"
        "    }\n"
        "  }\n"
        "  return sum;\n"
        "}\n"
    )
    result = engine.parse_file("utils.js", js_code, "javascript")
    assert len(result.symbols) >= 1
    func = result.symbols[0]
    assert func.name == "calculateTotal"
    assert result.total_complexity >= 2
