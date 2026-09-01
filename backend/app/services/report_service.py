from datetime import datetime, timezone
from typing import Dict, Any, List
from app.core.translations import localize_issue_item


class ReportService:
    """Generates professional Markdown and JSON executive reports from analysis results."""

    @classmethod
    def generate_markdown_report(
        cls,
        analysis_data: Dict[str, Any],
        repo_data: Dict[str, Any],
        issues: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
        metrics: List[Dict[str, Any]],
        language: str = "tr",
    ) -> str:
        repo_url = repo_data.get("url", "N/A")
        repo_name = repo_data.get("name", "Repository")
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        scores = {
            "overall": analysis_data.get("overall_score", 0),
            "architecture": analysis_data.get("architecture_score", 0),
            "security": analysis_data.get("security_score", 0),
            "performance": analysis_data.get("performance_score", 0),
            "quality": analysis_data.get("quality_score", 0),
            "maintainability": analysis_data.get("maintainability_score", 0),
        }

        # Issue counters
        crit = sum(1 for i in issues if i.get("severity") == "CRITICAL")
        high = sum(1 for i in issues if i.get("severity") == "HIGH")
        med = sum(1 for i in issues if i.get("severity") == "MEDIUM")
        low = sum(1 for i in issues if i.get("severity") == "LOW")

        is_tr = language.lower() == "tr"

        md = []
        if is_tr:
            md.append(f"# 🔍 CodeXray Yapay Zeka Kod Tabanı İstihbarat Raporu — {repo_name}")
            md.append(f"**Depo:** [{repo_url}]({repo_url}) | **Oluşturulma Tarihi:** {now_str} | **Commit:** `{analysis_data.get('commit_hash', 'main')[:8]}`\n")
            md.append("---")

            # Executive Scorecard
            md.append("## 📊 Yönetici Skor Kartı\n")
            md.append("| Metrik | Puan | Durum |")
            md.append("| :--- | :---: | :--- |")
            md.append(f"| **Genel Sağlık** | **{scores['overall']} / 100** | {'🟢 Mükemmel' if scores['overall'] >= 80 else '🟡 Geliştirilmeli' if scores['overall'] >= 60 else '🔴 Kritik Eylem Gerekli'} |")
            md.append(f"| Mimari | {scores['architecture']} / 100 | {'🟢 Güçlü' if scores['architecture'] >= 75 else '🟡 Yeniden Yapılandırma Gerekli'} |")
            md.append(f"| Güvenlik | {scores['security']} / 100 | {'🟢 Güvenli' if scores['security'] >= 80 else '🔴 Zafiyetler Bulundu'} |")
            md.append(f"| Performans | {scores['performance']} / 100 | {'🟢 Optimize' if scores['performance'] >= 75 else '🟡 Olası Darboğazlar'} |")
            md.append(f"| Kod Kalitesi | {scores['quality']} / 100 | {'🟢 Temiz' if scores['quality'] >= 75 else '🟡 Bakım / Teknik Borç'} |")
            md.append(f"| Sürdürülebilirlik | {scores['maintainability']} / 100 | {'🟢 Yüksek' if scores['maintainability'] >= 70 else '🟡 Düşük'} |\n")

            # Summary Metrics
            frameworks_str = ', '.join(analysis_data.get('project_frameworks', [])) or 'Tespit edilmedi'
            md.append("## 📁 Kod Tabanı Genel Bakışı\n")
            md.append(f"- **Ana Programlama Dili:** `{analysis_data.get('primary_language', 'N/A')}`")
            md.append(f"- **Toplam Taranan Dosya:** {analysis_data.get('total_files', 0)}")
            md.append(f"- **Kod Satırı Sayısı (LOC):** {analysis_data.get('total_code_lines', 0)}")
            md.append(f"- **Tespit Edilen Kütüphane / Çatılar:** {frameworks_str}")
            md.append(f"- **Tespit Edilen Bulgular:** {len(issues)} (🚨 {crit} Kritik, ⚠️ {high} Yüksek, 📋 {med} Orta, ℹ️ {low} Düşük)\n")

            # AI Summary
            if analysis_data.get("ai_summary"):
                md.append("## 🤖 Yapay Zeka Mimari ve Kod İnceleme Özeti\n")
                md.append(f"{analysis_data.get('ai_summary')}\n")

            # Top Critical / High Issues
            top_issues = [i for i in issues if i.get("severity") in ("CRITICAL", "HIGH")][:10]
            if top_issues:
                md.append("## 🚨 Yüksek Öncelikli Bulgular ve Eylem Planı\n")
                for idx, orig_iss in enumerate(top_issues, start=1):
                    iss = localize_issue_item(orig_iss, lang="tr")
                    md.append(f"### {idx}. [{iss.get('severity')}] {iss.get('title')}")
                    md.append(f"- **Kategori:** `{iss.get('category')}` | **Dosya:** `{iss.get('file_path')}:{iss.get('line_number')}`")
                    md.append(f"- **Açıklama:** {iss.get('description')}")
                    if iss.get("code_snippet"):
                        md.append(f"```text\n{iss.get('code_snippet')}\n```")
                    if iss.get("impact"):
                        md.append(f"- **Etki:** {iss.get('impact')}")
                    if iss.get("recommendation"):
                        md.append(f"- **Öneri:** {iss.get('recommendation')}")
                    if iss.get("suggested_fix"):
                        md.append(f"**Önerilen Düzeltme:**\n```python\n{iss.get('suggested_fix')}\n```\n")
                    md.append("")

            # Dependencies summary
            if dependencies:
                md.append("## 📦 Bağımlılıklar ve Güvenlik Açıkları\n")
                md.append(f"Toplam takip edilen bağımlılık: **{len(dependencies)}**\n")
                vuln_deps = [d for d in dependencies if d.get("vulnerabilities_count", 0) > 0]
                if vuln_deps:
                    md.append("| Bağımlılık | Ekosistem | Mevcut Sürüm | Zafiyetler |")
                    md.append("| :--- | :--- | :--- | :--- |")
                    for vd in vuln_deps:
                        md.append(f"| **{vd.get('name')}** | {vd.get('ecosystem')} | `{vd.get('version')}` | 🔴 {vd.get('vulnerabilities_count')} CVE |")
                    md.append("")

            md.append("---")
            md.append("*CodeXray tarafından otomatik olarak oluşturulmuştur.*")
        else:
            md.append(f"# AI Codebase Intelligence Report — {repo_name}")
            md.append(f"**Repository:** [{repo_url}]({repo_url}) | **Generated:** {now_str} | **Commit:** `{analysis_data.get('commit_hash', 'main')[:8]}`\n")
            md.append("---")

            # Executive Scorecard
            md.append("## 📊 Executive Scorecard\n")
            md.append("| Metric | Score | Status |")
            md.append("| :--- | :---: | :--- |")
            md.append(f"| **Overall Health** | **{scores['overall']} / 100** | {'🟢 Excellent' if scores['overall'] >= 80 else '🟡 Needs Improvement' if scores['overall'] >= 60 else '🔴 Critical Action Required'} |")
            md.append(f"| Architecture | {scores['architecture']} / 100 | {'🟢 Strong' if scores['architecture'] >= 75 else '🟡 Refactor Needed'} |")
            md.append(f"| Security | {scores['security']} / 100 | {'🟢 Secure' if scores['security'] >= 80 else '🔴 Vulnerabilities Found'} |")
            md.append(f"| Performance | {scores['performance']} / 100 | {'🟢 Optimized' if scores['performance'] >= 75 else '🟡 Potential Bottlenecks'} |")
            md.append(f"| Code Quality | {scores['quality']} / 100 | {'🟢 Clean' if scores['quality'] >= 75 else '🟡 Maintainability Debt'} |")
            md.append(f"| Maintainability | {scores['maintainability']} / 100 | {'🟢 High' if scores['maintainability'] >= 70 else '🟡 Low'} |\n")

            # Summary Metrics
            md.append("## 📁 Codebase Overview\n")
            md.append(f"- **Primary Language:** `{analysis_data.get('primary_language', 'N/A')}`")
            md.append(f"- **Total Scanned Files:** {analysis_data.get('total_files', 0)}")
            md.append(f"- **Lines of Code (LOC):** {analysis_data.get('total_code_lines', 0)}")
            md.append(f"- **Detected Frameworks:** {', '.join(analysis_data.get('project_frameworks', [])) or 'None detected'}")
            md.append(f"- **Discovered Issues:** {len(issues)} (🚨 {crit} Critical, ⚠️ {high} High, 📋 {med} Medium, ℹ️ {low} Low)\n")

            # AI Summary
            if analysis_data.get("ai_summary"):
                md.append("## 🤖 AI Architectural & Code Review Summary\n")
                md.append(f"{analysis_data.get('ai_summary')}\n")

            # Top Critical / High Issues
            top_issues = [i for i in issues if i.get("severity") in ("CRITICAL", "HIGH")][:10]
            if top_issues:
                md.append("## 🚨 High-Priority Findings & Action Items\n")
                for idx, iss in enumerate(top_issues, start=1):
                    md.append(f"### {idx}. [{iss.get('severity')}] {iss.get('title')}")
                    md.append(f"- **Category:** `{iss.get('category')}` | **File:** `{iss.get('file_path')}:{iss.get('line_number')}`")
                    md.append(f"- **Description:** {iss.get('description')}")
                    if iss.get("code_snippet"):
                        md.append(f"```text\n{iss.get('code_snippet')}\n```")
                    if iss.get("impact"):
                        md.append(f"- **Impact:** {iss.get('impact')}")
                    if iss.get("recommendation"):
                        md.append(f"- **Recommendation:** {iss.get('recommendation')}")
                    if iss.get("suggested_fix"):
                        md.append(f"**Suggested Fix:**\n```python\n{iss.get('suggested_fix')}\n```\n")
                    md.append("")

            # Dependencies summary
            if dependencies:
                md.append("## 📦 Dependencies & Vulnerabilities\n")
                md.append(f"Total dependencies tracked: **{len(dependencies)}**\n")
                vuln_deps = [d for d in dependencies if d.get("vulnerabilities_count", 0) > 0]
                if vuln_deps:
                    md.append("| Dependency | Ecosystem | Current Version | Vulnerabilities |")
                    md.append("| :--- | :--- | :--- | :--- |")
                    for vd in vuln_deps:
                        md.append(f"| **{vd.get('name')}** | {vd.get('ecosystem')} | `{vd.get('version')}` | 🔴 {vd.get('vulnerabilities_count')} CVEs |")
                    md.append("")

            md.append("---")
            md.append("*Generated automatically by CodeXray.*")

        return "\n".join(md)
