from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import logger
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    logger.info("Initializing database schemas...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down CodeXray backend.")


app = FastAPI(
    title="CodeXray API",
    version=settings.VERSION,
    description=(
        "**CodeXray** — Production-grade AI-powered code intelligence platform. "
        "Performs AST structural parsing, vulnerability scanning, latency diagnostics, "
        "and RAG semantic codebase chat."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all during dev/demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error handling {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please check logs."},
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Healthcheck endpoint for Kubernetes, Docker, and uptime monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "ai_provider": settings.AI_PROVIDER,
    }


# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)
