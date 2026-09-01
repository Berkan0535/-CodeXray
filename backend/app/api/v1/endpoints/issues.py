from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import AnalysisIssue, Analysis
from app.schemas.schemas import IssueResponse, IssueExplainRequest, IssueExplainResponse
from app.ai.reviewer import AIReviewer
from app.core.config import settings
from app.core.translations import localize_issue_item

router = APIRouter()


@router.get("/{analysis_id}/issues", response_model=List[IssueResponse])
async def list_analysis_issues(
    analysis_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW, INFO"),
    category: Optional[str] = Query(None, description="Filter by category: SECURITY, PERFORMANCE, QUALITY, ARCHITECTURE, DEPENDENCY"),
    search: Optional[str] = Query(None, description="Search query in title or description"),
    lang: str = Query("tr", description="Language code: 'tr' or 'en'"),
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Lists discovered issues for an analysis with rich filtering and pagination.
    """
    stmt = select(AnalysisIssue).where(AnalysisIssue.analysis_id == analysis_id)

    if severity:
        stmt = stmt.where(AnalysisIssue.severity == severity.upper())
    if category:
        stmt = stmt.where(AnalysisIssue.category == category.upper())
    if search:
        search_fmt = f"%{search.lower()}%"
        stmt = stmt.where(
            AnalysisIssue.title.ilike(search_fmt) |
            AnalysisIssue.description.ilike(search_fmt) |
            AnalysisIssue.file_path.ilike(search_fmt)
        )

    stmt = stmt.order_by(
        # Order by severity priority
        AnalysisIssue.severity.desc(),
        AnalysisIssue.file_path.asc()
    ).offset(offset).limit(limit)

    res = await db.execute(stmt)
    issues = res.scalars().all()

    if lang == "tr":
        localized_list = []
        for iss in issues:
            iss_dict = {
                "id": iss.id,
                "analysis_id": iss.analysis_id,
                "severity": iss.severity,
                "category": iss.category,
                "title": iss.title,
                "description": iss.description,
                "file_path": iss.file_path,
                "line_number": iss.line_number,
                "end_line_number": iss.end_line_number,
                "code_snippet": iss.code_snippet,
                "impact": iss.impact,
                "recommendation": iss.recommendation,
                "suggested_fix": iss.suggested_fix,
                "tool": iss.tool,
                "confidence": iss.confidence,
                "created_at": iss.created_at,
            }
            loc = localize_issue_item(iss_dict, lang="tr")
            localized_list.append(IssueResponse(**loc))
        return localized_list

    return issues


@router.post("/{analysis_id}/issues/{issue_id}/explain", response_model=IssueExplainResponse)
async def explain_issue(
    analysis_id: str,
    issue_id: str,
    payload: IssueExplainRequest,
    lang: str = Query("tr", description="Language code: 'tr' or 'en'"),
    db: AsyncSession = Depends(get_db)
):
    """
    Invokes AI to provide an in-depth breakdown of a specific issue,
    threat/impact explanation, and a clean suggested code fix.
    """
    stmt = select(AnalysisIssue).where(
        AnalysisIssue.id == issue_id,
        AnalysisIssue.analysis_id == analysis_id
    )
    res = await db.execute(stmt)
    issue = res.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue_dict = {
        "id": issue.id,
        "title": issue.title,
        "severity": issue.severity,
        "category": issue.category,
        "description": issue.description,
        "file_path": issue.file_path,
        "line_number": issue.line_number,
        "code_snippet": issue.code_snippet,
        "impact": issue.impact,
        "recommendation": issue.recommendation,
        "suggested_fix": issue.suggested_fix,
        "confidence": issue.confidence,
    }

    if lang == "tr":
        issue_dict = localize_issue_item(issue_dict, lang="tr")

    result = await AIReviewer.explain_issue(
        issue_data=issue_dict,
        user_question=payload.question,
        provider_type=settings.AI_PROVIDER,
        language=lang
    )

    return IssueExplainResponse(
        issue_id=issue.id,
        explanation=result["explanation"],
        detailed_impact=result["detailed_impact"],
        suggested_code=result.get("suggested_code"),
        confidence_note=result["confidence_note"],
    )
