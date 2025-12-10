"""
Background Scheduler Service

APScheduler-based scheduler for background sync operations.
Features:
- Time window enforcement (e.g., 19:00 - 07:00)
- Multi-day sync support for large tables
- Automatic job management
- Graceful shutdown
"""

from datetime import datetime, time, timedelta
from typing import Any, Callable
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.core.config import settings


class BackgroundScheduler:
    """
    Background Sync Scheduler

    Manages scheduled background sync jobs using APScheduler.
    Enforces time windows and handles multi-day syncs.
    """

    def __init__(self):
        """Initialize scheduler with APScheduler"""
        self._scheduler: AsyncIOScheduler | None = None
        self._running = False
        self._jobs: dict[str, str] = {}  # entity_name -> job_id

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running and self._scheduler is not None

    def _create_scheduler(self) -> AsyncIOScheduler:
        """Create APScheduler instance with configuration"""
        jobstores = {
            'default': MemoryJobStore()
        }

        executors = {
            'default': AsyncIOExecutor()
        }

        job_defaults = {
            'coalesce': True,  # Combine missed runs into one
            'max_instances': 1,  # Only one instance per job
            'misfire_grace_time': 3600,  # 1 hour grace for misfires
        }

        scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC',
        )

        return scheduler

    async def start(self) -> None:
        """
        Start the scheduler

        Creates APScheduler instance and starts background loop.
        """
        if self._running:
            logger.warning("Scheduler already running")
            return

        if not settings.BACKGROUND_SYNC_ENABLED:
            logger.info("Background sync disabled in settings")
            return

        logger.info("Starting background scheduler...")

        try:
            self._scheduler = self._create_scheduler()
            self._scheduler.start()
            self._running = True

            logger.info("Background scheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    async def stop(self) -> None:
        """
        Stop the scheduler gracefully

        Waits for running jobs to complete before shutdown.
        """
        if not self._running:
            logger.warning("Scheduler not running")
            return

        logger.info("Stopping background scheduler...")

        try:
            if self._scheduler:
                self._scheduler.shutdown(wait=True)
                self._scheduler = None

            self._running = False
            self._jobs.clear()

            logger.info("Background scheduler stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
            raise

    def add_sync_job(
        self,
        entity_name: str,
        job_func: Callable,
        schedule_config: dict[str, Any],
        job_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """
        Add a background sync job

        Args:
            entity_name: Entity name (used as job identifier)
            job_func: Async function to execute
            schedule_config: Schedule configuration dict with:
                - sync_window_start: Start time (HH:MM:SS)
                - sync_window_end: End time (HH:MM:SS)
                - interval_minutes: Run interval within window (default: 60)
            job_kwargs: Arguments to pass to job function

        Returns:
            Job ID

        Raises:
            RuntimeError: If scheduler not running
            ValueError: If job already exists
        """
        if not self.is_running:
            raise RuntimeError("Scheduler not running")

        if entity_name in self._jobs:
            raise ValueError(f"Job already exists for entity: {entity_name}")

        logger.info(f"Adding sync job for entity: {entity_name}")

        # Parse time window
        window_start = self._parse_time(schedule_config.get("sync_window_start", "19:00:00"))
        window_end = self._parse_time(schedule_config.get("sync_window_end", "07:00:00"))
        interval_minutes = schedule_config.get("interval_minutes", 60)

        # Create cron trigger for window start
        # Job runs every day at window_start time
        trigger = CronTrigger(
            hour=window_start.hour,
            minute=window_start.minute,
            timezone='UTC',
        )

        job = self._scheduler.add_job(
            self._create_windowed_job(job_func, window_start, window_end, interval_minutes),
            trigger=trigger,
            id=f"sync_{entity_name}",
            name=f"Background sync: {entity_name}",
            kwargs=job_kwargs or {},
            replace_existing=True,
        )

        self._jobs[entity_name] = job.id
        logger.info(f"Added sync job: {job.id}, trigger: daily at {window_start}")

        return job.id

    def add_interval_job(
        self,
        job_id: str,
        job_func: Callable,
        interval_minutes: int = 60,
        job_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """
        Add an interval-based job (for retries, cleanups, etc.)

        Args:
            job_id: Unique job identifier
            job_func: Async function to execute
            interval_minutes: Run interval in minutes
            job_kwargs: Arguments to pass to job function

        Returns:
            Job ID
        """
        if not self.is_running:
            raise RuntimeError("Scheduler not running")

        logger.info(f"Adding interval job: {job_id}, interval: {interval_minutes}m")

        trigger = IntervalTrigger(minutes=interval_minutes)

        job = self._scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name=job_id,
            kwargs=job_kwargs or {},
            replace_existing=True,
        )

        logger.info(f"Added interval job: {job.id}")
        return job.id

    def add_one_time_job(
        self,
        job_id: str,
        job_func: Callable,
        run_at: datetime,
        job_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """
        Add a one-time job

        Args:
            job_id: Unique job identifier
            job_func: Async function to execute
            run_at: When to run the job
            job_kwargs: Arguments to pass to job function

        Returns:
            Job ID
        """
        if not self.is_running:
            raise RuntimeError("Scheduler not running")

        logger.info(f"Adding one-time job: {job_id}, run_at: {run_at}")

        trigger = DateTrigger(run_date=run_at)

        job = self._scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name=job_id,
            kwargs=job_kwargs or {},
            replace_existing=True,
        )

        logger.info(f"Added one-time job: {job.id}")
        return job.id

    def remove_job(self, entity_name: str) -> bool:
        """
        Remove a sync job

        Args:
            entity_name: Entity name

        Returns:
            True if removed, False if not found
        """
        if not self.is_running:
            return False

        job_id = self._jobs.get(entity_name)
        if not job_id:
            return False

        try:
            self._scheduler.remove_job(job_id)
            del self._jobs[entity_name]
            logger.info(f"Removed sync job for entity: {entity_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove job: {e}")
            return False

    def pause_job(self, entity_name: str) -> bool:
        """
        Pause a sync job

        Args:
            entity_name: Entity name

        Returns:
            True if paused, False if not found
        """
        if not self.is_running:
            return False

        job_id = self._jobs.get(entity_name)
        if not job_id:
            return False

        try:
            self._scheduler.pause_job(job_id)
            logger.info(f"Paused sync job for entity: {entity_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to pause job: {e}")
            return False

    def resume_job(self, entity_name: str) -> bool:
        """
        Resume a paused sync job

        Args:
            entity_name: Entity name

        Returns:
            True if resumed, False if not found
        """
        if not self.is_running:
            return False

        job_id = self._jobs.get(entity_name)
        if not job_id:
            return False

        try:
            self._scheduler.resume_job(job_id)
            logger.info(f"Resumed sync job for entity: {entity_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to resume job: {e}")
            return False

    def get_job_status(self, entity_name: str) -> dict[str, Any] | None:
        """
        Get job status

        Args:
            entity_name: Entity name

        Returns:
            Job status dict or None if not found
        """
        if not self.is_running:
            return None

        job_id = self._jobs.get(entity_name)
        if not job_id:
            return None

        try:
            job = self._scheduler.get_job(job_id)
            if not job:
                return None

            return {
                "job_id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "pending": job.pending,
            }

        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    def list_jobs(self) -> list[dict[str, Any]]:
        """
        List all scheduled jobs

        Returns:
            List of job status dicts
        """
        if not self.is_running:
            return []

        jobs = []
        for entity_name, job_id in self._jobs.items():
            status = self.get_job_status(entity_name)
            if status:
                status["entity_name"] = entity_name
                jobs.append(status)

        return jobs

    def _create_windowed_job(
        self,
        job_func: Callable,
        window_start: time,
        window_end: time,
        interval_minutes: int,
    ) -> Callable:
        """
        Create a wrapper that enforces time window

        The wrapper checks if current time is within window before executing.

        Args:
            job_func: Original job function
            window_start: Window start time
            window_end: Window end time
            interval_minutes: Interval between runs

        Returns:
            Wrapped async function
        """
        async def windowed_job(**kwargs):
            """Execute job only within time window"""
            current_time = datetime.utcnow().time()

            if not self._is_within_window(current_time, window_start, window_end):
                logger.debug(
                    f"Outside sync window ({window_start}-{window_end}), "
                    f"current: {current_time}"
                )
                return

            logger.info(f"Executing sync job within window ({window_start}-{window_end})")

            try:
                await job_func(**kwargs)
            except Exception as e:
                logger.error(f"Sync job failed: {e}")
                raise

        return windowed_job

    @staticmethod
    def _is_within_window(current: time, window_start: time, window_end: time) -> bool:
        """
        Check if current time is within sync window

        Handles overnight windows (e.g., 19:00 - 07:00)

        Args:
            current: Current time
            window_start: Window start time
            window_end: Window end time

        Returns:
            True if within window
        """
        if window_start <= window_end:
            # Same day window (e.g., 09:00 - 17:00)
            return window_start <= current <= window_end
        else:
            # Overnight window (e.g., 19:00 - 07:00)
            return current >= window_start or current <= window_end

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """
        Parse time string to time object

        Args:
            time_str: Time string (HH:MM:SS or HH:MM)

        Returns:
            time object
        """
        if isinstance(time_str, time):
            return time_str

        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0

        return time(hour=hour, minute=minute, second=second)


# Global scheduler instance
background_scheduler = BackgroundScheduler()
