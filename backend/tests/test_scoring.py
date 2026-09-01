import pytest
from app.services.scoring_service import ScoringService


def test_scoring_calculation_clean_codebase():
    scores = ScoringService.calculate_scores(
        issues=[],
        arch_result={"architecture_score": 90.0},
        quality_result={"scores": {"code_quality": 88.0, "maintainability": 85.0}},
        perf_issues=[],
        sec_issues=[],
    )
    assert scores["overall_score"] >= 80.0
    assert scores["security_score"] == 100.0
    assert scores["performance_score"] == 100.0


def test_scoring_calculation_with_critical_issues():
    sec_issues = [
        {"severity": "CRITICAL", "title": "SQL Injection"},
        {"severity": "HIGH", "title": "Command Injection"},
    ]
    scores = ScoringService.calculate_scores(
        issues=sec_issues,
        arch_result={"architecture_score": 90.0},
        quality_result={"scores": {"code_quality": 88.0, "maintainability": 85.0}},
        perf_issues=[],
        sec_issues=sec_issues,
    )
    # Critical security issues cap overall score
    assert scores["overall_score"] <= 72.0
    assert scores["security_score"] < 70.0
