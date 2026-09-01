from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import Dependency, Analysis
from app.schemas.schemas import DependencyResponse

router = APIRouter()


@router.get("/{analysis_id}/dependencies", response_model=List[DependencyResponse])
async def list_dependencies(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns detected ecosystem dependencies (npm, pip, go, maven, cargo)
    along with known CVE vulnerability alerts and outdated flags.
    """
    stmt = select(Dependency).where(Dependency.analysis_id == analysis_id).order_by(Dependency.name.asc())
    res = await db.execute(stmt)
    return res.scalars().all()
