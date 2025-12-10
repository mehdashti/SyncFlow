"""
Schedule API Router

Endpoints for managing background sync schedules.
"""

from datetime import datetime
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.session import get_session
from app.schemas.schedule_schemas import (
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleResponse,
    ScheduleListResponse,
    SchedulerStatusResponse,
    ScheduleStatsResponse,
    TriggerSyncRequest,
    TriggerSyncResponse,
)
from app.repositories.schedule_repository import ScheduleRepository
from app.services.scheduler.scheduler import background_scheduler
from app.services.scheduler.jobs import BackgroundSyncJob
from app.core.config import settings


router = APIRouter(prefix=f"{settings.API_PREFIX}/schedules", tags=["Schedules"])


def _to_response(schedule: dict) -> ScheduleResponse:
    """Convert schedule dict to response model"""
    total = schedule.get("total_rows_estimate") or 0
    current = schedule.get("current_offset") or 0
    progress = (current / total * 100) if total > 0 else 0

    return ScheduleResponse(
        uid=schedule["uid"],
        entity_name=schedule["entity_name"],
        source_system=schedule["source_system"],
        is_enabled=schedule["is_enabled"],
        sync_window_start=schedule["sync_window_start"],
        sync_window_end=schedule["sync_window_end"],
        days_to_complete=schedule["days_to_complete"],
        rows_per_day=schedule.get("rows_per_day"),
        total_rows_estimate=schedule.get("total_rows_estimate"),
        current_offset=current,
        progress_percent=round(progress, 2),
        last_run_at=datetime.fromisoformat(schedule["last_run_at"]) if schedule.get("last_run_at") else None,
        next_run_at=datetime.fromisoformat(schedule["next_run_at"]) if schedule.get("next_run_at") else None,
        created_at=datetime.fromisoformat(schedule["created_at"]) if schedule.get("created_at") else datetime.utcnow(),
        updated_at=datetime.fromisoformat(schedule["updated_at"]) if schedule.get("updated_at") else None,
    )


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    session: AsyncSession = Depends(get_session),
):
    """
    Get scheduler service status

    Returns current status of the background scheduler including
    running jobs and their next run times.
    """
    logger.debug("Getting scheduler status")

    repo = ScheduleRepository(session)

    # Get enabled schedules count
    schedules = await repo.list_schedules(is_enabled=True)
    enabled_count = len(schedules)

    # Get active jobs
    jobs = background_scheduler.list_jobs()

    return SchedulerStatusResponse(
        is_running=background_scheduler.is_running,
        enabled_schedules=enabled_count,
        active_jobs=len(jobs),
        jobs=jobs,
    )


@router.get("/stats", response_model=ScheduleStatsResponse)
async def get_schedule_stats(
    session: AsyncSession = Depends(get_session),
):
    """
    Get schedule statistics

    Returns aggregate statistics across all schedules.
    """
    logger.debug("Getting schedule statistics")

    repo = ScheduleRepository(session)
    stats = await repo.get_statistics()

    return ScheduleStatsResponse(
        total_schedules=stats["total_schedules"],
        enabled_schedules=stats["enabled_schedules"],
        disabled_schedules=stats["disabled_schedules"],
        average_progress_percent=stats["average_progress_percent"],
    )


@router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    is_enabled: bool | None = Query(default=None, description="Filter by enabled status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all background sync schedules

    Returns paginated list of configured schedules.
    """
    logger.debug(f"Listing schedules: enabled={is_enabled}, page={page}")

    repo = ScheduleRepository(session)

    offset = (page - 1) * page_size
    schedules = await repo.list_schedules(
        is_enabled=is_enabled,
        limit=page_size,
        offset=offset,
    )

    # Get total count
    all_schedules = await repo.list_schedules(is_enabled=is_enabled, limit=10000)
    total = len(all_schedules)
    pages = ceil(total / page_size) if total > 0 else 1

    items = [_to_response(s) for s in schedules]

    return ScheduleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{schedule_uid}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_uid: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get schedule by UID

    Returns detailed information about a specific schedule.
    """
    logger.debug(f"Getting schedule: {schedule_uid}")

    repo = ScheduleRepository(session)
    schedule = await repo.get_schedule(schedule_uid)

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return _to_response(schedule)


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    request: ScheduleCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new background sync schedule

    Configures a new entity for multi-day background sync.
    """
    logger.info(f"Creating schedule for entity: {request.entity_name}")

    repo = ScheduleRepository(session)

    # Check if schedule already exists
    existing = await repo.get_schedule_by_entity(request.entity_name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Schedule already exists for entity: {request.entity_name}"
        )

    # Parse times
    from datetime import time
    start_parts = request.sync_window_start.split(":")
    end_parts = request.sync_window_end.split(":")
    window_start = time(int(start_parts[0]), int(start_parts[1]) if len(start_parts) > 1 else 0)
    window_end = time(int(end_parts[0]), int(end_parts[1]) if len(end_parts) > 1 else 0)

    schedule = await repo.create_schedule(
        entity_name=request.entity_name,
        source_system=request.source_system,
        sync_window_start=window_start,
        sync_window_end=window_end,
        days_to_complete=request.days_to_complete,
        rows_per_day=request.rows_per_day,
        total_rows_estimate=request.total_rows_estimate,
        is_enabled=request.is_enabled,
    )

    # Register job with scheduler if enabled
    if request.is_enabled and background_scheduler.is_running:
        try:
            job = BackgroundSyncJob(
                entity_name=request.entity_name,
                source_system=request.source_system,
                rows_per_day=schedule.get("rows_per_day"),
            )

            background_scheduler.add_sync_job(
                entity_name=request.entity_name,
                job_func=job.execute,
                schedule_config={
                    "sync_window_start": request.sync_window_start,
                    "sync_window_end": request.sync_window_end,
                },
            )
            logger.info(f"Registered scheduler job for: {request.entity_name}")
        except Exception as e:
            logger.warning(f"Failed to register scheduler job: {e}")

    return _to_response(schedule)


@router.patch("/{schedule_uid}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_uid: str,
    request: ScheduleUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Update a schedule

    Updates schedule configuration. Changes take effect on next run.
    """
    logger.info(f"Updating schedule: {schedule_uid}")

    repo = ScheduleRepository(session)

    # Check if exists
    existing = await repo.get_schedule(schedule_uid)
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Build update dict from non-None values
    update_data = {}
    if request.sync_window_start is not None:
        from datetime import time
        parts = request.sync_window_start.split(":")
        update_data["sync_window_start"] = time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    if request.sync_window_end is not None:
        from datetime import time
        parts = request.sync_window_end.split(":")
        update_data["sync_window_end"] = time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    if request.days_to_complete is not None:
        update_data["days_to_complete"] = request.days_to_complete
    if request.rows_per_day is not None:
        update_data["rows_per_day"] = request.rows_per_day
    if request.total_rows_estimate is not None:
        update_data["total_rows_estimate"] = request.total_rows_estimate
    if request.is_enabled is not None:
        update_data["is_enabled"] = request.is_enabled

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    schedule = await repo.update_schedule(schedule_uid, **update_data)

    # Update scheduler job if enabled status changed
    if request.is_enabled is not None:
        entity_name = schedule["entity_name"]
        if request.is_enabled:
            if background_scheduler.is_running:
                background_scheduler.resume_job(entity_name)
        else:
            if background_scheduler.is_running:
                background_scheduler.pause_job(entity_name)

    return _to_response(schedule)


@router.delete("/{schedule_uid}", status_code=204)
async def delete_schedule(
    schedule_uid: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a schedule

    Removes schedule and stops associated background job.
    """
    logger.info(f"Deleting schedule: {schedule_uid}")

    repo = ScheduleRepository(session)

    # Get schedule for entity name
    schedule = await repo.get_schedule(schedule_uid)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Remove from scheduler
    if background_scheduler.is_running:
        background_scheduler.remove_job(schedule["entity_name"])

    # Delete from database
    deleted = await repo.delete_schedule(schedule_uid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")


@router.post("/{schedule_uid}/reset", response_model=ScheduleResponse)
async def reset_schedule_progress(
    schedule_uid: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Reset schedule progress

    Resets current_offset to 0 to start a new full sync cycle.
    """
    logger.info(f"Resetting schedule progress: {schedule_uid}")

    repo = ScheduleRepository(session)

    # Check if exists
    existing = await repo.get_schedule(schedule_uid)
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule = await repo.reset_progress(schedule_uid)

    return _to_response(schedule)


@router.post("/{schedule_uid}/trigger", response_model=TriggerSyncResponse)
async def trigger_sync(
    schedule_uid: str,
    request: TriggerSyncRequest = TriggerSyncRequest(),
    session: AsyncSession = Depends(get_session),
):
    """
    Manually trigger a scheduled sync

    Runs the sync job immediately, optionally ignoring the time window.
    """
    logger.info(f"Triggering sync for schedule: {schedule_uid}, force={request.force}")

    repo = ScheduleRepository(session)

    # Get schedule
    schedule = await repo.get_schedule(schedule_uid)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if not schedule["is_enabled"]:
        raise HTTPException(status_code=400, detail="Schedule is disabled")

    # Check time window unless force=True
    if not request.force:
        from datetime import time as dt_time
        current_time = datetime.utcnow().time()

        # Parse window times
        start_str = schedule["sync_window_start"]
        end_str = schedule["sync_window_end"]
        start_parts = start_str.split(":")
        end_parts = end_str.split(":")
        window_start = dt_time(int(start_parts[0]), int(start_parts[1]) if len(start_parts) > 1 else 0)
        window_end = dt_time(int(end_parts[0]), int(end_parts[1]) if len(end_parts) > 1 else 0)

        # Check window (handle overnight)
        in_window = False
        if window_start <= window_end:
            in_window = window_start <= current_time <= window_end
        else:
            in_window = current_time >= window_start or current_time <= window_end

        if not in_window:
            raise HTTPException(
                status_code=400,
                detail=f"Outside sync window ({start_str}-{end_str}). Use force=true to override."
            )

    # Create and run job
    entity_name = schedule["entity_name"]
    job = BackgroundSyncJob(
        entity_name=entity_name,
        source_system=schedule["source_system"],
        rows_per_day=schedule.get("rows_per_day"),
    )

    # Add one-time job to run immediately
    job_id = f"sync_{entity_name}_manual_{int(datetime.utcnow().timestamp())}"

    if background_scheduler.is_running:
        background_scheduler.add_one_time_job(
            job_id=job_id,
            job_func=job.execute,
            run_at=datetime.utcnow(),
        )

        return TriggerSyncResponse(
            success=True,
            message="Sync job scheduled to run immediately",
            job_id=job_id,
            scheduled_for=datetime.utcnow(),
        )
    else:
        # Scheduler not running, execute directly
        logger.info("Scheduler not running, executing job directly")
        result = await job.execute()

        return TriggerSyncResponse(
            success=result.get("status") == "success",
            message=f"Sync executed directly: {result.get('status')}",
            job_id=None,
            scheduled_for=None,
        )


@router.post("/start", status_code=200)
async def start_scheduler():
    """
    Start the background scheduler

    Starts the APScheduler service and loads all enabled schedules.
    """
    logger.info("Starting background scheduler via API")

    if background_scheduler.is_running:
        return {"message": "Scheduler already running"}

    await background_scheduler.start()

    return {"message": "Scheduler started successfully"}


@router.post("/stop", status_code=200)
async def stop_scheduler():
    """
    Stop the background scheduler

    Gracefully stops the scheduler, waiting for running jobs to complete.
    """
    logger.info("Stopping background scheduler via API")

    if not background_scheduler.is_running:
        return {"message": "Scheduler not running"}

    await background_scheduler.stop()

    return {"message": "Scheduler stopped successfully"}
