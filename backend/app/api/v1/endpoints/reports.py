from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import Analysis, Repository, AnalysisIssue, Dependency, AnalysisMetric
from app.schemas.schemas import ReportResponse, AnalysisResponse, IssueResponse, DependencyResponse, MetricResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/{analysis_id}/report")
async def get_report(
    analysis_id: str,
    format: str = Query("json", description="Output format: 'json' or 'markdown'"),
    lang: str = Query("tr", description="Language code: 'tr' or 'en'"),
    db: AsyncSession = Depends(get_db)
):
    """
    Exports a comprehensive code intelligence report in JSON or Markdown format.
    """
    stmt = (
        select(Analysis)
        .options(
            selectinload(Analysis.repository),
            selectinload(Analysis.issues),
            selectinload(Analysis.dependencies),
            selectinload(Analysis.metrics),
        )
        .where(Analysis.id == analysis_id)
    )
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    repo_dict = {
        "url": analysis.repository.url if analysis.repository else "",
        "name": analysis.repository.name if analysis.repository else "Repository",
    }
    analysis_dict = {
        "overall_score": analysis.overall_score,
        "architecture_score": analysis.architecture_score,
        "security_score": analysis.security_score,
        "performance_score": analysis.performance_score,
        "quality_score": analysis.quality_score,
        "maintainability_score": analysis.maintainability_score,
        "primary_language": analysis.primary_language,
        "total_files": analysis.total_files,
        "total_code_lines": analysis.total_code_lines,
        "project_frameworks": analysis.project_frameworks or [],
        "commit_hash": analysis.commit_hash,
        "ai_summary": analysis.ai_summary,
    }
    issues_list = [
        {
            "severity": i.severity,
            "category": i.category,
            "title": i.title,
            "description": i.description,
            "file_path": i.file_path,
            "line_number": i.line_number,
            "code_snippet": i.code_snippet,
            "impact": i.impact,
            "recommendation": i.recommendation,
            "suggested_fix": i.suggested_fix,
        }
        for i in analysis.issues
    ]
    deps_list = [
        {
            "name": d.name,
            "version": d.version,
            "ecosystem": d.ecosystem,
            "vulnerabilities_count": d.vulnerabilities_count,
        }
        for d in analysis.dependencies
    ]
    metrics_list = [
        {
            "name": m.name,
            "category": m.category,
            "value": m.value,
        }
        for m in analysis.metrics
    ]

    md_report = ReportService.generate_markdown_report(
        analysis_data=analysis_dict,
        repo_data=repo_dict,
        issues=issues_list,
        dependencies=deps_list,
        metrics=metrics_list,
        language=lang,
    )

    if format.lower() == "markdown":
        return PlainTextResponse(md_report, media_type="text/markdown")

    # JSON output
    issues_summary = {
        "critical": analysis.critical_issues_count,
        "high": analysis.high_issues_count,
        "medium": analysis.medium_issues_count,
        "low": analysis.low_issues_count,
    }

    return ReportResponse(
        analysis=AnalysisResponse.model_validate(analysis),
        issues_summary=issues_summary,
        top_issues=[IssueResponse.model_validate(i) for i in analysis.issues[:15]],
        metrics=[MetricResponse.model_validate(m) for m in analysis.metrics],
        dependencies=[DependencyResponse.model_validate(d) for d in analysis.dependencies],
        architecture_summary={"layers": ["frontend", "api", "service", "repository", "database", "infra", "core"]},
        markdown_report=md_report,
    )
