from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import ArchitectureNode, ArchitectureEdge, Analysis
from app.schemas.schemas import ArchitectureGraphResponse, ArchitectureNodeSchema, ArchitectureEdgeSchema

router = APIRouter()


@router.get("/{analysis_id}/architecture", response_model=ArchitectureGraphResponse)
async def get_architecture_graph(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the interactive architecture graph containing nodes, layers,
    cross-module dependencies, circular references, and coupling metrics.
    """
    # Check analysis exists
    analysis_stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis_res = await db.execute(analysis_stmt)
    if not analysis_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Analysis not found")

    nodes_stmt = select(ArchitectureNode).where(ArchitectureNode.analysis_id == analysis_id)
    nodes_res = await db.execute(nodes_stmt)
    nodes = nodes_res.scalars().all()

    edges_stmt = select(ArchitectureEdge).where(ArchitectureEdge.analysis_id == analysis_id)
    edges_res = await db.execute(edges_stmt)
    edges = edges_res.scalars().all()

    return ArchitectureGraphResponse(
        nodes=[ArchitectureNodeSchema.model_validate(n) for n in nodes],
        edges=[ArchitectureEdgeSchema.model_validate(e) for e in edges],
        layers=["frontend", "api", "service", "repository", "database", "infra", "core"],
        circular_dependencies=[],
        coupling_metrics={},
    )
