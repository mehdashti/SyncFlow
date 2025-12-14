"""
SyncFlow - Main Application Entry Point

FastAPI application for data integration between APISmith and ScheduleHub.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.logging import configure_logging
# from app.db.session import engine, dispose_engine
# from app.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context."""
    logger.info("SyncFlow starting up...")

    # Start background sync scheduler
    if settings.BACKGROUND_SYNC_ENABLED:
        from app.services.scheduler.scheduler import background_scheduler
        try:
            await background_scheduler.start()
            logger.info("Background scheduler started")
        except Exception as e:
            logger.warning(f"Failed to start background scheduler: {e}")

    yield

    logger.info("SyncFlow shutting down...")

    # Stop background scheduler
    if settings.BACKGROUND_SYNC_ENABLED:
        from app.services.scheduler.scheduler import background_scheduler
        try:
            await background_scheduler.stop()
            logger.info("Background scheduler stopped")
        except Exception as e:
            logger.warning(f"Failed to stop background scheduler: {e}")


# Configure logging
configure_logging()

# Create FastAPI application
app = FastAPI(
    title="SyncFlow",
    version="2.0.0",
    description="Data Integration Microservice - APISmith to ScheduleHub SyncFlow",
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SyncFlow",
        "version": "2.0.0",
        "status": "operational",
        "docs": f"{settings.API_PREFIX}/docs",
    }


@app.get(f"{settings.API_PREFIX}/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SyncFlow",
        "version": "2.0.0",
        "environment": settings.APP_ENV,
    }


@app.get(f"{settings.API_PREFIX}/metadata")
async def metadata():
    """Service metadata endpoint."""
    return {
        "app": "SyncFlow",
        "version": "2.0.0",
        "environment": settings.APP_ENV,
        "database": {
            "host": settings.POSTGRES_HOST,
            "database": settings.POSTGRES_DB,
            "schema": settings.POSTGRES_SCHEMA,
        },
        "apismith": {
            "url": settings.APISmith_URL,
        },
        "schedulehub": {
            "url": settings.ScheduleHub_URL,
        },
    }


# Include routers
from app.routers import sync_router, monitoring_router, entity_router, mapping_router
from app.routers import schedule_router

app.include_router(sync_router.router)
app.include_router(monitoring_router.router)
app.include_router(entity_router.router)
app.include_router(mapping_router.router)
app.include_router(schedule_router.router)

logger.info(f"SyncFlow initialized on {settings.API_HOST}:{settings.API_PORT}")
