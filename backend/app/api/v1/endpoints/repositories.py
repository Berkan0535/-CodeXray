import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.logging import logger
from app.core.security import is_safe_repo_url
from app.models.entities import Repository, Analysis
from app.schemas.schemas import (
    RepositoryResponse,
    AnalysisCreate,
    AnalysisResponse,
)
from app.services.repo_manager import RepoManager
from app.services.pipeline_service import PipelineService
from app.tasks.celery_app import run_codebase_analysis_task

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_repository(
    payload: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a repository URL for asynchronous architectural, security,
    performance, and code quality analysis.
    """
    url = payload.repository_url.strip()
    is_safe, err_msg = is_safe_repo_url(url)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security check failed for repository URL: {err_msg}"
        )

    owner, repo_name = RepoManager.parse_repo_info(url)
    branch = payload.branch or "main"

    # Find or create repository entity
    stmt = select(Repository).where(Repository.url == url)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()

    if not repo:
        repo = Repository(
            url=url,
            name=repo_name,
            owner=owner,
            default_branch=branch
        )
        db.add(repo)
        await db.commit()
        await db.refresh(repo)

    # Create new queued Analysis record
    analysis = Analysis(
        repository_id=repo.id,
        status="queued",
        stage="QUEUED",
        progress_percent=0,
        branch=branch,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # Dispatch to background runner
    if settings.USE_CELERY:
        logger.info(f"Dispatching analysis {analysis.id} to Celery worker...")
        run_codebase_analysis_task.delay(analysis.id, settings.AI_PROVIDER)
    else:
        logger.info(f"Dispatching analysis {analysis.id} to background asyncio task...")
        background_tasks.add_task(PipelineService.run_pipeline, analysis.id, settings.AI_PROVIDER)

    # Attach repository relation for response
    analysis.repository = repo
    return analysis


from sqlalchemy.orm import selectinload

@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Lists all repositories analyzed by the platform with latest analysis metrics."""
    stmt = (
        select(Repository)
        .options(selectinload(Repository.analyses))
        .order_by(desc(Repository.updated_at))
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    repos = res.scalars().all()

    result = []
    for repo in repos:
        analyses_sorted = sorted(repo.analyses, key=lambda a: a.created_at, reverse=True) if repo.analyses else []
        latest = analyses_sorted[0] if analyses_sorted else None
        latest_completed = next((a for a in analyses_sorted if a.status == "completed"), None)
        active_analysis = latest_completed or latest

        repo_dict = {
            "id": repo.id,
            "url": repo.url,
            "name": repo.name,
            "owner": repo.owner,
            "default_branch": repo.default_branch,
            "created_at": repo.created_at,
            "updated_at": repo.updated_at,
            "last_analyzed_at": repo.last_analyzed_at or (latest.created_at if latest else None),
            "latest_analysis_id": active_analysis.id if active_analysis else None,
            "latest_status": latest.status if latest else None,
            "overall_score": active_analysis.overall_score if active_analysis else None,
            "critical_issues_count": active_analysis.critical_issues_count if active_analysis else 0,
            "high_issues_count": active_analysis.high_issues_count if active_analysis else 0,
            "primary_language": active_analysis.primary_language if active_analysis else None,
            "total_files": active_analysis.total_files if active_analysis else 0,
            "total_lines": active_analysis.total_lines if active_analysis else 0,
            "total_code_lines": active_analysis.total_code_lines if active_analysis else 0,
            "analyses_count": len(analyses_sorted),
        }
        result.append(RepositoryResponse(**repo_dict))
    return result


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetches metadata and latest analysis summary for a single repository."""
    stmt = select(Repository).options(selectinload(Repository.analyses)).where(Repository.id == repository_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    analyses_sorted = sorted(repo.analyses, key=lambda a: a.created_at, reverse=True) if repo.analyses else []
    latest = analyses_sorted[0] if analyses_sorted else None
    latest_completed = next((a for a in analyses_sorted if a.status == "completed"), None)
    active_analysis = latest_completed or latest

    repo_dict = {
        "id": repo.id,
        "url": repo.url,
        "name": repo.name,
        "owner": repo.owner,
        "default_branch": repo.default_branch,
        "created_at": repo.created_at,
        "updated_at": repo.updated_at,
        "last_analyzed_at": repo.last_analyzed_at or (latest.created_at if latest else None),
        "latest_analysis_id": active_analysis.id if active_analysis else None,
        "latest_status": latest.status if latest else None,
        "overall_score": active_analysis.overall_score if active_analysis else None,
        "critical_issues_count": active_analysis.critical_issues_count if active_analysis else 0,
        "high_issues_count": active_analysis.high_issues_count if active_analysis else 0,
        "primary_language": active_analysis.primary_language if active_analysis else None,
        "total_files": active_analysis.total_files if active_analysis else 0,
        "total_lines": active_analysis.total_lines if active_analysis else 0,
        "total_code_lines": active_analysis.total_code_lines if active_analysis else 0,
        "analyses_count": len(analyses_sorted),
    }
    return RepositoryResponse(**repo_dict)


@router.get("/{repository_id}/analyses", response_model=List[AnalysisResponse])
async def list_repository_analyses(
    repository_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Lists all historical analyses for a specific repository."""
    stmt = (
        select(Analysis)
        .options(selectinload(Analysis.repository))
        .where(Analysis.repository_id == repository_id)
        .order_by(desc(Analysis.created_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
