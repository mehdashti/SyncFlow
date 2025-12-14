"""
Monitoring API Router

Endpoints for system monitoring and statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from math import ceil

from app.db.session import get_session
from app.schemas.monitoring_schemas import (
    StatisticsResponse,
    BatchStatistics,
    FailedRecordStatistics,
    PendingChildStatistics,
    FailedRecordResponse,
    FailedRecordListResponse,
    PendingChildResponse,
    PendingChildListResponse,
)
from app.repositories.batch_repository import BatchRepository
from app.repositories.failed_record_repository import FailedRecordRepository
from app.services.resolver.engine import ParentChildResolver
from app.core.config import settings
from datetime import datetime


router = APIRouter(prefix=f"{settings.API_PREFIX}/monitoring", tags=["Monitoring"])


@router.get("/stats", response_model=StatisticsResponse)
async def get_statistics(
    session: AsyncSession = Depends(get_session),
):
    """
    Get overall system statistics

    Returns statistics for:
    - Batches (by status and entity)
    - Failed records (by error type, stage, entity)
    - Pending children (by parent and entity)

    **Returns:**
    - 200: System statistics
    - 500: Server error
    """
    try:
        batch_repo = BatchRepository(session)
        failed_repo = FailedRecordRepository(session)
        resolver = ParentChildResolver(session)

        # Get batch statistics
        batch_stats_raw = await batch_repo.get_batch_statistics()
        batch_stats = BatchStatistics(
            total_batches=batch_stats_raw["total_batches"],
            by_status=batch_stats_raw["by_status"],
            by_entity=batch_stats_raw["by_entity"],
        )

        # Get failed record statistics
        failed_stats_raw = await failed_repo.get_failed_record_statistics()
        failed_stats = FailedRecordStatistics(
            total_failed=failed_stats_raw["total_failed"],
            by_error_type=failed_stats_raw["by_error_type"],
            by_stage=failed_stats_raw["by_stage"],
            by_entity=failed_stats_raw["by_entity"],
            retryable=failed_stats_raw["retryable"],
            max_retry_exceeded=failed_stats_raw["max_retry_exceeded"],
        )

        # Get pending children statistics
        pending_stats_raw = await resolver.get_pending_statistics()
        pending_stats = PendingChildStatistics(
            total_pending=pending_stats_raw["total_pending"],
            by_parent=pending_stats_raw["by_parent"],
            by_entity=pending_stats_raw["by_entity"],
            max_retry_exceeded=pending_stats_raw["max_retry_exceeded"],
        )

        return StatisticsResponse(
            batches=batch_stats,
            failed_records=failed_stats,
            pending_children=pending_stats,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/failed-records", response_model=FailedRecordListResponse)
async def get_failed_records(
    batch_uid: str | None = Query(None, description="Filter by batch UID"),
    entity_name: str | None = Query(None, description="Filter by entity name"),
    error_type: str | None = Query(None, description="Filter by error type"),
    stage: str | None = Query(None, description="Filter by pipeline stage"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get failed records with pagination

    **Query Parameters:**
    - batch_uid: Filter by batch (optional)
    - entity_name: Filter by entity (optional)
    - error_type: Filter by error type (optional)
    - stage: Filter by pipeline stage (optional)
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)

    **Returns:**
    - 200: Paginated failed records
    - 400: Invalid parameters
    - 500: Server error
    """
    if page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be <= 100")

    try:
        failed_repo = FailedRecordRepository(session)

        # Calculate offset
        offset = (page - 1) * page_size

        # Get failed records
        records = await failed_repo.list_failed_records(
            batch_uid=batch_uid,
            entity_name=entity_name,
            error_type=error_type,
            stage=stage,
            limit=page_size,
            offset=offset,
        )

        # Get statistics for total count
        stats = await failed_repo.get_failed_record_statistics()
        total = stats["total_failed"]

        # Build response
        items = [
            FailedRecordResponse(
                uid=r["uid"],
                batch_uid=r["batch_uid"],
                entity_name=r["entity_name"],
                record_data=r["record_data"],
                error_type=r["error_type"],
                error_message=r["error_message"],
                stage=r["stage"],
                retry_count=r["retry_count"],
                last_retry_at=datetime.fromisoformat(r["last_retry_at"]) if r["last_retry_at"] else None,
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in records
        ]

        return FailedRecordListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total > 0 else 0,
        )

    except Exception as e:
        logger.error(f"Failed to get failed records: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get failed records: {str(e)}")


@router.get("/pending-children", response_model=PendingChildListResponse)
async def get_pending_children(
    parent_entity: str | None = Query(None, description="Filter by parent entity"),
    entity_name: str | None = Query(None, description="Filter by child entity name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get pending children with pagination

    **Query Parameters:**
    - parent_entity: Filter by parent entity (optional)
    - entity_name: Filter by child entity (optional)
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)

    **Returns:**
    - 200: Paginated pending children
    - 400: Invalid parameters
    - 500: Server error
    """
    if page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be <= 100")

    try:
        resolver = ParentChildResolver(session)

        # Get pending children (simplified - real implementation needs pagination in resolver)
        limit = page_size
        records = await resolver.get_pending_children(
            parent_entity=parent_entity,
            limit=limit,
        )

        # Get statistics for total count
        stats = await resolver.get_pending_statistics()
        total = stats["total_pending"]

        # Build response
        items = [
            PendingChildResponse(
                uid=r["uid"],
                batch_uid=r["batch_uid"],
                entity_name=r["entity_name"],
                child_bk_hash=r["child_bk_hash"],
                child_data=r["child_data"],
                parent_entity=r["parent_entity"],
                parent_bk_hash=r["parent_bk_hash"],
                retry_count=r["retry_count"],
                reason=r["reason"],
                last_retry_at=None,  # TODO: Add to schema
                created_at=r["created_at"],
            )
            for r in records
        ]

        return PendingChildListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total > 0 else 0,
        )

    except Exception as e:
        logger.error(f"Failed to get pending children: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending children: {str(e)}")


@router.get("/health/detailed")
async def detailed_health_check(
    session: AsyncSession = Depends(get_session),
):
    """
    Detailed health check with dependency status

    Checks:
    - Database connectivity
    - APISmith availability (TODO)
    - ScheduleHub availability (TODO)

    **Returns:**
    - 200: Health status with details
    - 503: Service unhealthy
    """
    health_status = {
        "service": "SyncFlow",
        "version": "2.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # Check database
    try:
        from sqlalchemy import text
        result = await session.execute(text("SELECT 1"))
        await result.fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Connected",
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        health_status["status"] = "unhealthy"

    # TODO: Check APISmith
    health_status["checks"]["apismith"] = {
        "status": "unknown",
        "message": "Check not implemented",
    }

    # TODO: Check ScheduleHub
    health_status["checks"]["schedulehub"] = {
        "status": "unknown",
        "message": "Check not implemented",
    }

    # Determine overall status
    if health_status["status"] == "unhealthy":
        return HTTPException(status_code=503, detail=health_status)

    return health_status


@router.get("/metrics/prometheus")
async def prometheus_metrics(
    session: AsyncSession = Depends(get_session),
):
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text format.

    **TODO:** Implement full Prometheus metrics with prometheus_client library.

    **Returns:**
    - 200: Prometheus metrics (text format)
    - 500: Server error
    """
    try:
        batch_repo = BatchRepository(session)
        failed_repo = FailedRecordRepository(session)

        # Get statistics
        batch_stats = await batch_repo.get_batch_statistics()
        failed_stats = await failed_repo.get_failed_record_statistics()

        # Build Prometheus metrics (simplified)
        metrics = []

        # Batch metrics
        metrics.append("# HELP syncflow_batches_total Total number of sync batches")
        metrics.append("# TYPE syncflow_batches_total gauge")
        metrics.append(f"syncflow_batches_total {batch_stats['total_batches']}")

        # Batch by status
        metrics.append("# HELP syncflow_batches_by_status Number of batches by status")
        metrics.append("# TYPE syncflow_batches_by_status gauge")
        for status, count in batch_stats["by_status"].items():
            metrics.append(f'syncflow_batches_by_status{{status="{status}"}} {count}')

        # Failed records
        metrics.append("# HELP syncflow_failed_records_total Total number of failed records")
        metrics.append("# TYPE syncflow_failed_records_total gauge")
        metrics.append(f"syncflow_failed_records_total {failed_stats['total_failed']}")

        # Retryable failed records
        metrics.append("# HELP syncflow_failed_records_retryable Number of retryable failed records")
        metrics.append("# TYPE syncflow_failed_records_retryable gauge")
        metrics.append(f"syncflow_failed_records_retryable {failed_stats['retryable']}")

        return "\n".join(metrics)

    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")
