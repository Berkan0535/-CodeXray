import os
import asyncio
from celery import Celery
from app.core.config import settings
from app.core.logging import logger

celery_app = Celery(
    "codebase_analyst_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.ANALYSIS_TIMEOUT_SECONDS + 60,
)


@celery_app.task(name="tasks.run_codebase_analysis")
def run_codebase_analysis_task(analysis_id: str, provider_type: str = "mock"):
    """Celery background task entrypoint."""
    logger.info(f"Celery worker picked up analysis {analysis_id}")
    from app.services.pipeline_service import PipelineService
    
    # Run async pipeline inside event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(PipelineService.run_pipeline(analysis_id, provider_type))
    finally:
        loop.close()
