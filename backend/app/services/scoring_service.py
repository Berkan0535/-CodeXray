from typing import List, Dict, Any


class ScoringService:
    """
    Computes deterministic, reproducible multi-factor engineering scores (0-100)
    for Architecture, Security, Performance, Quality, Maintainability, and Overall Codebase Health.
    """

    @classmethod
    def calculate_scores(
        cls,
        issues: List[Dict[str, Any]],
        arch_result: Dict[str, Any],
        quality_result: Dict[str, Any],
        perf_issues: List[Dict[str, Any]],
        sec_issues: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        # 1. Security Score (Starts at 100)
        sec_score = 100.0
        crit_count = 0
        high_count = 0
        med_count = 0
        low_count = 0

        for iss in sec_issues:
            sev = str(iss.get("severity", "")).upper()
            if sev == "CRITICAL":
                crit_count += 1
                sec_score -= 22.0
            elif sev == "HIGH":
                high_count += 1
                sec_score -= 10.0
            elif sev == "MEDIUM":
                med_count += 1
                sec_score -= 4.0
            elif sev == "LOW":
                low_count += 1
                sec_score -= 1.0

        sec_score = max(10.0, min(100.0, sec_score))

        # 2. Performance Score (Starts at 100)
        perf_score = 100.0
        for iss in perf_issues:
            sev = str(iss.get("severity", "")).upper()
            if sev == "HIGH":
                perf_score -= 12.0
            elif sev == "MEDIUM":
                perf_score -= 6.0
            else:
                perf_score -= 2.0

        perf_score = max(15.0, min(100.0, perf_score))

        # 3. Architecture Score
        arch_score = arch_result.get("architecture_score", 85.0)

        # 4. Quality & Maintainability Scores
        quality_scores = quality_result.get("scores", {})
        code_quality_score = quality_scores.get("code_quality", 80.0)
        maintainability_score = quality_scores.get("maintainability", 80.0)

        # 5. Overall Score Formula (Weighted Composite)
        overall_raw = (
            sec_score * 0.25 +
            arch_score * 0.20 +
            perf_score * 0.20 +
            code_quality_score * 0.20 +
            maintainability_score * 0.15
        )

        # Penalize overall score if critical security vulnerabilities exist
        if crit_count > 0:
            overall_raw = min(72.0, overall_raw)

        overall_score = round(max(10.0, min(100.0, overall_raw)), 1)

        return {
            "overall_score": overall_score,
            "architecture_score": round(arch_score, 1),
            "security_score": round(sec_score, 1),
            "performance_score": round(perf_score, 1),
            "quality_score": round(code_quality_score, 1),
            "maintainability_score": round(maintainability_score, 1),
        }
