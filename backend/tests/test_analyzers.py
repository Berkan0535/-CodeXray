import os
import pytest
from app.analyzers.file_scanner import FileScanner, ScannedFile
from app.analyzers.language_detector import LanguageDetector
from app.analyzers.project_detector import ProjectDetector
from app.analyzers.quality.quality_analyzer import QualityAnalyzer
from app.analyzers.dependencies.dependency_analyzer import DependencyAnalyzer
from app.analyzers.architecture.architecture_analyzer import ArchitectureAnalyzer
from app.analyzers.parser.ast_extractor import TreeSitterParserEngine


def test_file_scanner_and_languages(tmp_path):
    # Create sample files
    (tmp_path / "main.py").write_text("print('hello')\n# comment\n", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log('js');\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("console.log('ignored');", encoding="utf-8")

    files = FileScanner.scan_directory(str(tmp_path))
    rel_paths = [f.relative_path for f in files]
    
    assert "main.py" in rel_paths
    assert "app.js" in rel_paths
    assert not any("node_modules" in p for p in rel_paths)

    lang_res = LanguageDetector.detect_languages(files)
    assert lang_res["primary_language"] in ("Python", "JavaScript")
    assert "Python" in lang_res["languages"]
    assert "JavaScript" in lang_res["languages"]


def test_project_detector(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi==0.115.0\nsqlalchemy>=2.0.0\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")

    files = FileScanner.scan_directory(str(tmp_path))
    proj_res = ProjectDetector.detect(str(tmp_path), files)

    assert "FastAPI" in proj_res["frameworks"]
    assert "Docker" in proj_res["infrastructure"]
    assert "pip/poetry/uv" in proj_res["build_tools"]


def test_dependency_analyzer(tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.20.0\nlodash==4.17.15\n", encoding="utf-8")
    
    scanned_file = ScannedFile(
        relative_path="requirements.txt",
        absolute_path=str(req_file),
        size_bytes=40,
        total_lines=2,
        code_lines=2,
        extension=".txt"
    )

    deps, issues = DependencyAnalyzer.analyze(str(tmp_path), [scanned_file])
    assert len(deps) >= 2
    assert len(issues) >= 1  # requests 2.20.0 has CVE


def test_quality_and_architecture_analyzer():
    engine = TreeSitterParserEngine()
    py_code = (
        "def complex_function(a, b, c):\n"
        "    if a:\n"
        "        if b:\n"
        "            if c:\n"
        "                return 1\n"
        "    return 0\n"
    )
    ast_res = engine.parse_file("services/billing.py", py_code, "python")
    scanned = ScannedFile("services/billing.py", "services/billing.py", len(py_code), 6, 6, 0, 0, False, ".py")

    quality = QualityAnalyzer.analyze([scanned], [ast_res])
    assert quality["scores"]["code_quality"] > 0
    assert quality["maintainability_index"] > 0

    arch = ArchitectureAnalyzer.analyze([scanned], [ast_res])
    assert "service" in arch["layers"]
    assert len(arch["nodes"]) >= 1
