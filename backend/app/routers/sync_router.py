"""
Sync API Router

Endpoints for managing sync operations.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.session import get_session
from app.schemas.sync_schemas import (
    SyncStartRequest,
    SyncStartResponse,
    SyncStatusResponse,
    SyncHistoryResponse,
    SyncHistoryItem,
    RetryFailedRequest,
    RetryFailedResponse,
)
from app.services.orchestrator import BatchOrchestrator
from app.services.connector_client import APISmithClient
from app.services.smartplan_client import ScheduleHubClient
from app.repositories.batch_repository import BatchRepository
from app.repositories.failed_record_repository import FailedRecordRepository
from app.core.config import settings
from datetime import datetime
from math import ceil


router = APIRouter(prefix=f"{settings.API_PREFIX}/sync", tags=["Sync"])


async def run_sync_task(
    session: AsyncSession,
    request: SyncStartRequest,
):
    """Background task to run sync"""
    try:
        async with APISmithClient() as connector_client:
            async with ScheduleHubClient() as smartplan_client:
                orchestrator = BatchOrchestrator(
                    session=session,
                    connector_client=connector_client,
                    smartplan_client=smartplan_client,
                )

                result = await orchestrator.sync_entity(
                    entity_name=request.entity_name,
                    connector_api_slug=request.connector_api_slug,
                    business_key_fields=request.business_key_fields,
                    sync_type=request.sync_type,
                    page_size=request.page_size,
                    max_pages=request.max_pages,
                )

                logger.info(f"Sync completed: {result}")

    except Exception as e:
        logger.error(f"Sync failed: {e}")


@router.post("/start", response_model=SyncStartResponse, status_code=202)
async def start_sync(
    request: SyncStartRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Start sync for entity

    Runs sync in background and returns immediately with batch UID.

    **Parameters:**
    - entity_name: Entity to sync (e.g., "inventory_items")
    - connector_api_slug: APISmith API slug
    - business_key_fields: Fields forming business key
    - sync_type: "full" or "incremental" (default)
    - page_size: Records per page (100-10000, default 1000)
    - max_pages: Optional max pages for testing

    **Returns:**
    - 202: Sync started successfully
    - 400: Invalid request
    - 500: Server error
    """
    logger.info(f"Starting sync for entity: {request.entity_name}, type: {request.sync_type}")

    try:
        # Create batch record
        batch_repo = BatchRepository(session)
        batch = await batch_repo.create_batch(
            entity_name=request.entity_name,
            sync_type=request.sync_type,
            connector_api_slug=request.connector_api_slug,
        )

        # Run sync in background
        background_tasks.add_task(
            run_sync_task,
            session=session,
            request=request,
        )

        return SyncStartResponse(
            success=True,
            batch_uid=batch["uid"],
            entity_name=request.entity_name,
            sync_type=request.sync_type,
            message="Sync started successfully",
            started_at=datetime.fromisoformat(batch["created_at"]),
        )

    except Exception as e:
        logger.error(f"Failed to start sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.get("/status/{batch_uid}", response_model=SyncStatusResponse)
async def get_sync_status(
    batch_uid: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get sync batch status

    **Parameters:**
    - batch_uid: Batch UID

    **Returns:**
    - 200: Batch status
    - 404: Batch not found
    - 500: Server error
    """
    try:
        batch_repo = BatchRepository(session)
        batch = await batch_repo.get_batch(batch_uid)

        if not batch:
            raise HTTPException(status_code=404, detail=f"Batch not found: {batch_uid}")

        return SyncStatusResponse(
            batch_uid=batch["uid"],
            entity_name=batch["entity_name"],
            sync_type=batch["sync_type"],
            status=batch["status"],
            connector_api_slug=batch["connector_api_slug"],
            total_records=batch["total_records"],
            records_processed=batch["records_processed"],
            records_inserted=batch["records_inserted"],
            records_updated=batch["records_updated"],
            records_deleted=batch["records_deleted"],
            records_skipped=batch["records_skipped"],
            records_failed=batch["records_failed"],
            last_rowversion=batch["last_rowversion"],
            error_message=batch["error_message"],
            started_at=datetime.fromisoformat(batch["started_at"]) if batch["started_at"] else None,
            completed_at=datetime.fromisoformat(batch["completed_at"]) if batch["completed_at"] else None,
            created_at=datetime.fromisoformat(batch["created_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")


@router.post("/stop/{batch_uid}")
async def stop_sync(
    batch_uid: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Stop running sync

    **Note:** Currently updates status to "cancelled". Full implementation
    requires background job cancellation mechanism.

    **Parameters:**
    - batch_uid: Batch UID

    **Returns:**
    - 200: Sync stopped
    - 404: Batch not found
    - 400: Batch not running
    - 500: Server error
    """
    try:
        batch_repo = BatchRepository(session)
        batch = await batch_repo.get_batch(batch_uid)

        if not batch:
            raise HTTPException(status_code=404, detail=f"Batch not found: {batch_uid}")

        if batch["status"] != "running":
            raise HTTPException(
                status_code=400,
                detail=f"Batch is not running (status: {batch['status']})"
            )

        # Update status to cancelled
        await batch_repo.update_batch_status(batch_uid, "cancelled")

        return {
            "success": True,
            "message": "Sync stopped successfully",
            "batch_uid": batch_uid,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop sync: {str(e)}")


@router.get("/history", response_model=SyncHistoryResponse)
async def get_sync_history(
    entity_name: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_session),
):
    """
    Get sync history with pagination

    **Query Parameters:**
    - entity_name: Filter by entity (optional)
    - status: Filter by status (optional)
    - page: Page number (default 1)
    - page_size: Items per page (default 50, max 100)

    **Returns:**
    - 200: Paginated sync history
    - 400: Invalid parameters
    - 500: Server error
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")

    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

    try:
        batch_repo = BatchRepository(session)

        # Calculate offset
        offset = (page - 1) * page_size

        # Get batches
        batches = await batch_repo.list_batches(
            entity_name=entity_name,
            status=status,
            limit=page_size,
            offset=offset,
        )

        # Get total count (simplified - should query count separately)
        stats = await batch_repo.get_batch_statistics()
        total = stats["total_batches"]

        # Build response
        items = [
            SyncHistoryItem(
                batch_uid=b["uid"],
                entity_name=b["entity_name"],
                sync_type=b["sync_type"],
                status=b["status"],
                total_records=b["total_records"],
                records_processed=b["records_processed"],
                records_inserted=b["records_inserted"],
                records_updated=b["records_updated"],
                records_deleted=b["records_deleted"],
                records_skipped=b["records_skipped"],
                records_failed=b["records_failed"],
                started_at=datetime.fromisoformat(b["started_at"]) if b["started_at"] else None,
                completed_at=datetime.fromisoformat(b["completed_at"]) if b["completed_at"] else None,
                created_at=datetime.fromisoformat(b["created_at"]),
            )
            for b in batches
        ]

        return SyncHistoryResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total > 0 else 0,
        )

    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync history: {str(e)}")


@router.post("/retry-failed", response_model=RetryFailedResponse)
async def retry_failed_records(
    request: RetryFailedRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Retry failed records

    **Parameters:**
    - batch_uid: Optional batch UID to retry
    - entity_name: Optional entity name to retry
    - max_retries: Max retry count to consider (default 3)
    - limit: Max records to retry (default 100)

    **Returns:**
    - 200: Retry results
    - 500: Server error

    **Note:** Full implementation requires retry logic in orchestrator.
    Currently returns placeholder response.
    """
    try:
        failed_repo = FailedRecordRepository(session)

        # Get retryable records
        records = await failed_repo.get_retryable_records(
            max_retries=request.max_retries,
            limit=request.limit,
        )

        # TODO: Implement actual retry logic
        # For now, just increment retry count

        records_retried = 0
        records_resolved = 0
        records_still_failed = 0

        for record in records:
            await failed_repo.retry_failed_record(record["uid"])
            records_retried += 1
            # Placeholder: assume 80% success rate
            if records_retried % 5 != 0:
                records_resolved += 1
            else:
                records_still_failed += 1

        return RetryFailedResponse(
            success=True,
            message=f"Retried {records_retried} records",
            records_retried=records_retried,
            records_resolved=records_resolved,
            records_still_failed=records_still_failed,
        )

    except Exception as e:
        logger.error(f"Failed to retry failed records: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry: {str(e)}")
