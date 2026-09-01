import os
from typing import Dict, Any, List, Optional
from app.ai.factory import AIProviderFactory
from app.core.security import wrap_untrusted_code
from app.core.logging import logger


class AIReviewer:
    """
    Coordinates multi-section modular AI code reviews,
    issue explanations, and prompt injection defense.
    """

    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

    @classmethod
    def _read_prompt(cls, filename: str) -> str:
        path = os.path.join(cls.PROMPTS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load prompt template {filename}: {e}")
            return "{{context}}"

    @classmethod
    async def generate_codebase_review(
        cls,
        summary_context: Dict[str, Any],
        provider_type: Optional[str] = None,
        language: str = "tr"
    ) -> Dict[str, Any]:
        provider = AIProviderFactory.get_provider(provider_type)
        is_tr = language.lower() == "tr"
        lang_instruction = "\n\nÖNEMLİ: Lütfen tüm yanıtınızı, başlıkları ve tavsiyeleri Türkçe olarak üretin." if is_tr else ""

        # 1. Architecture Section
        arch_prompt_tpl = cls._read_prompt("architecture.txt")
        arch_ctx = (
            f"Primary Language: {summary_context.get('primary_language')}\n"
            f"Frameworks: {', '.join(summary_context.get('frameworks', []))}\n"
            f"Databases: {', '.join(summary_context.get('databases', []))}\n"
            f"Total Files: {summary_context.get('total_files')}, Total LOC: {summary_context.get('total_code_lines')}\n"
            f"Layers Detected: {', '.join(summary_context.get('layers', []))}\n"
            f"Circular Dependencies Count: {len(summary_context.get('circular_dependencies', []))}\n"
        )
        arch_prompt = arch_prompt_tpl.replace("{{context}}", wrap_untrusted_code(arch_ctx, "METRICS")) + lang_instruction
        arch_review = await provider.generate_text(arch_prompt)

        # 2. Security Section
        sec_prompt_tpl = cls._read_prompt("security.txt")
        sec_issues = summary_context.get("security_issues", [])[:8]
        sec_ctx = "\n".join(
            f"- [{iss.get('severity')}] {iss.get('title')} in {iss.get('file_path')}:{iss.get('line_number')} ({iss.get('description')})"
            for iss in sec_issues
        ) or ("Statik taramada kritik güvenlik açığı bulunamadı." if is_tr else "No critical security vulnerabilities found in static scan.")
        sec_prompt = sec_prompt_tpl.replace("{{context}}", wrap_untrusted_code(sec_ctx, "FINDINGS")) + lang_instruction
        sec_review = await provider.generate_text(sec_prompt)

        # 3. Performance Section
        perf_prompt_tpl = cls._read_prompt("performance.txt")
        perf_issues = summary_context.get("performance_issues", [])[:8]
        perf_ctx = "\n".join(
            f"- [{iss.get('severity')}] {iss.get('title')} in {iss.get('file_path')}:{iss.get('line_number')} ({iss.get('description')})"
            for iss in perf_issues
        ) or ("Kritik performans darboğazı tespit edilmedi." if is_tr else "No critical performance bottlenecks identified.")
        perf_prompt = perf_prompt_tpl.replace("{{context}}", wrap_untrusted_code(perf_ctx, "FINDINGS")) + lang_instruction
        perf_review = await provider.generate_text(perf_prompt)

        # 4. Quality Section
        qual_prompt_tpl = cls._read_prompt("quality.txt")
        qual_metrics = summary_context.get("quality_metrics", {})
        qual_ctx = (
            f"Maintainability Index: {qual_metrics.get('maintainability_index', 80)}/100\n"
            f"Average Cyclomatic Complexity: {qual_metrics.get('avg_complexity', 1.5)}\n"
            f"Max Complexity: {qual_metrics.get('max_complexity', 1)}\n"
            f"Code Duplication Rate: {qual_metrics.get('duplication_percentage', 0)}%\n"
            f"Comment Ratio: {qual_metrics.get('comment_ratio', 10)}%\n"
        )
        qual_prompt = qual_prompt_tpl.replace("{{context}}", wrap_untrusted_code(qual_ctx, "METRICS")) + lang_instruction
        qual_review = await provider.generate_text(qual_prompt)

        # 5. High-level AI Executive Summary
        if is_tr:
            executive_summary = (
                f"{summary_context.get('repo_name', 'Proje')} için Yapay Zeka Kod Tabanı İncelemesi tamamlandı. "
                f"Kod tabanı {summary_context.get('total_files', 0)} dosya ({summary_context.get('total_code_lines', 0)} satır kod) içermektedir "
                f"ve ağırlıklı olarak {summary_context.get('primary_language', 'Bilinmeyen')} dilindedir. "
                f"Öne çıkan güçlü yönler arasında {len(summary_context.get('layers', []))} mimari katman boyunca modüler yapı bulunmaktadır. "
                f"Önerilen odak alanları: {len(sec_issues)} güvenlik uyarısını gidermek ve veritabanı sorgu kalıplarını optimize etmektir."
            )
        else:
            executive_summary = (
                f"AI Codebase Review completed for {summary_context.get('repo_name', 'project')}. "
                f"The codebase comprises {summary_context.get('total_files', 0)} files ({summary_context.get('total_code_lines', 0)} LOC) "
                f"primarily in {summary_context.get('primary_language', 'Unknown')}. "
                f"Key strengths include modular structure across {len(summary_context.get('layers', []))} architectural layers. "
                f"Recommended focus areas: address {len(sec_issues)} security alerts and optimize database query patterns."
            )

        return {
            "ai_summary": executive_summary,
            "sections": {
                "architecture": arch_review,
                "security": sec_review,
                "performance": perf_review,
                "quality": qual_review,
            }
        }

    @classmethod
    async def explain_issue(
        cls,
        issue_data: Dict[str, Any],
        user_question: Optional[str] = None,
        provider_type: Optional[str] = None,
        language: str = "tr"
    ) -> Dict[str, Any]:
        provider = AIProviderFactory.get_provider(provider_type)
        tpl = cls._read_prompt("explain_issue.txt")
        is_tr = language.lower() == "tr"

        context = (
            f"Title: {issue_data.get('title')}\n"
            f"Severity: {issue_data.get('severity')}\n"
            f"Category: {issue_data.get('category')}\n"
            f"File: {issue_data.get('file_path')}:{issue_data.get('line_number')}\n"
            f"Description: {issue_data.get('description')}\n"
            f"Code Snippet:\n{issue_data.get('code_snippet', 'N/A')}\n"
            f"Impact: {issue_data.get('impact', 'N/A')}\n"
            f"Recommendation: {issue_data.get('recommendation', 'N/A')}\n"
        )

        default_q = "Bu kod neden problemli ve bunu nasıl düzeltmeliyim?" if is_tr else "Why is this code a problem and how should I fix it?"
        q = user_question or default_q
        lang_instruction = "\n\nÖNEMLİ: Lütfen açıklamanızı, kök nedeni ve önerilerinizi Türkçe olarak yazın." if is_tr else ""
        prompt = tpl.replace("{{context}}", wrap_untrusted_code(context, "ISSUE")).replace("{{question}}", q) + lang_instruction
        explanation = await provider.generate_text(prompt)

        default_impact = "Olası güvenlik açığı veya bakım zorluğu." if is_tr else "Potential vulnerability or maintainability degradation."
        conf_note = (
            f"Güvenilirlik: {issue_data.get('confidence', 'YÜKSEK')}. Birleştirmeden önce test ortamında doğrulayın."
            if is_tr else
            f"Confidence: {issue_data.get('confidence', 'HIGH')}. Review in test environment before merging."
        )

        return {
            "issue_id": issue_data.get("id", ""),
            "explanation": explanation,
            "detailed_impact": issue_data.get("impact") or default_impact,
            "suggested_code": issue_data.get("suggested_fix"),
            "confidence_note": conf_note,
        }
