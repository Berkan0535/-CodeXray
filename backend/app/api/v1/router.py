from fastapi import APIRouter
from app.api.v1.endpoints import (
    repositories,
    analyses,
    issues,
    architecture,
    dependencies,
    metrics,
    chat,
    reports,
)

api_router = APIRouter()

api_router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["Analyses"])
api_router.include_router(issues.router, prefix="/analyses", tags=["Issues"])
api_router.include_router(architecture.router, prefix="/analyses", tags=["Architecture"])
api_router.include_router(dependencies.router, prefix="/analyses", tags=["Dependencies"])
api_router.include_router(metrics.router, prefix="/analyses", tags=["Metrics"])
api_router.include_router(chat.router, prefix="/analyses", tags=["Chat & RAG"])
api_router.include_router(reports.router, prefix="/analyses", tags=["Reports"])
