import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.entities import Analysis, Repository
from app.schemas.schemas import AnalysisResponse, AnalysisStatusResponse
from app.services.pipeline_service import PipelineService
from app.tasks.celery_app import run_codebase_analysis_task

router = APIRouter()


from typing import List, Optional
from sqlalchemy import desc

@router.get("", response_model=List[AnalysisResponse])
async def list_all_analyses(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Lists all recent analyses across all repositories."""
    stmt = (
        select(Analysis)
        .options(selectinload(Analysis.repository))
        .order_by(desc(Analysis.created_at))
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full analysis results, scores, issue counts, and metadata."""
    stmt = (
        select(Analysis)
        .options(selectinload(Analysis.repository))
        .where(Analysis.id == analysis_id)
    )
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        # Fallback if a repository_id was passed instead of analysis_id
        stmt_repo = (
            select(Analysis)
            .options(selectinload(Analysis.repository))
            .where(Analysis.repository_id == analysis_id)
            .order_by(desc(Analysis.created_at))
        )
        res_repo = await db.execute(stmt_repo)
        analysis = res_repo.scalars().first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis record not found")
    return analysis


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Poll endpoint for lightweight real-time stage and progress polling."""
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        # Fallback if repository_id was passed
        stmt_repo = select(Analysis).where(Analysis.repository_id == analysis_id).order_by(desc(Analysis.created_at))
        res_repo = await db.execute(stmt_repo)
        analysis = res_repo.scalars().first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis record not found")
    return analysis


@router.get("/{analysis_id}/events")
async def stream_analysis_events(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events (SSE) stream delivering real-time progress updates to frontend.
    """
    async def event_generator():
        while True:
            stmt = select(Analysis).where(Analysis.id == analysis_id)
            res = await db.execute(stmt)
            analysis = res.scalar_one_or_none()
            if not analysis:
                yield "data: {\"error\": \"Not found\"}\n\n"
                break

            data = (
                f'{{"id": "{analysis.id}", '
                f'"status": "{analysis.status}", '
                f'"stage": "{analysis.stage}", '
                f'"progress_percent": {analysis.progress_percent}, '
                f'"error_message": "{analysis.error_message or ""}"}}'
            )
            yield f"data: {data}\n\n"

            if analysis.status in ("completed", "failed"):
                break
            await asyncio.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{analysis_id}/reanalyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def reanalyze(
    analysis_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Triggers a fresh re-analysis for an existing analysis record."""
    stmt = select(Analysis).options(selectinload(Analysis.repository)).where(Analysis.id == analysis_id)
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis.status = "queued"
    analysis.stage = "QUEUED"
    analysis.progress_percent = 0
    analysis.error_message = None
    await db.commit()
    await db.refresh(analysis)

    if settings.USE_CELERY:
        run_codebase_analysis_task.delay(analysis.id, settings.AI_PROVIDER)
    else:
        background_tasks.add_task(PipelineService.run_pipeline, analysis.id, settings.AI_PROVIDER)

    return analysis
