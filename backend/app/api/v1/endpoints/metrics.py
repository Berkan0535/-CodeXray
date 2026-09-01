from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import AnalysisMetric, Analysis
from app.schemas.schemas import MetricResponse

router = APIRouter()


@router.get("/{analysis_id}/metrics", response_model=List[MetricResponse])
async def get_metrics(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns granular quality, maintainability, and complexity metrics for an analysis.
    """
    stmt = select(AnalysisMetric).where(AnalysisMetric.analysis_id == analysis_id)
    res = await db.execute(stmt)
    return res.scalars().all()
