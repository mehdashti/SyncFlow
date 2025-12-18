"""
Schedule Repository

Handles background_sync_schedule table operations using SQLAlchemy Core.
Manages background sync schedules with time windows and multi-day sync configuration.
"""

from datetime import datetime, time
from typing import Any
from uuid import UUID
from loguru import logger
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import background_sync_schedule_table
from app.core.uuid_utils import generate_uuid7


class ScheduleRepository:
    """
    Background Sync Schedule Repository

    Manages background sync schedules using SQLAlchemy Core.
    NO ORM - uses Table API for all operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository

        Args:
            session: Async database session
        """
        self.session = session

    async def create_schedule(
        self,
        entity_name: str,
        source_system: str,
        sync_window_start: time | None = None,
        sync_window_end: time | None = None,
        days_to_complete: int = 7,
        rows_per_day: int | None = None,
        total_rows_estimate: int | None = None,
        is_enabled: bool = True,
    ) -> dict[str, Any]:
        """
        Create new background sync schedule

        Args:
            entity_name: Entity to sync (e.g., "inventory_items")
            source_system: Source system identifier
            sync_window_start: Start of sync window (default: 19:00)
            sync_window_end: End of sync window (default: 07:00)
            days_to_complete: Number of days to complete full sync
            rows_per_day: Target rows per day (calculated if not provided)
            total_rows_estimate: Estimated total rows
            is_enabled: Whether schedule is enabled

        Returns:
            Created schedule record

        Raises:
            Exception: If creation fails
        """
        logger.info(
            f"Creating schedule: entity={entity_name}, source={source_system}, "
            f"days={days_to_complete}"
        )

        try:
            # Generate UUID v7
            uid = generate_uuid7()

            # Calculate rows_per_day if total_rows_estimate provided
            if total_rows_estimate and not rows_per_day:
                rows_per_day = total_rows_estimate // days_to_complete

            values = {
                "uid": uid,
                "entity_name": entity_name,
                "source_system": source_system,
                "is_enabled": is_enabled,
                "days_to_complete": days_to_complete,
                "rows_per_day": rows_per_day,
                "total_rows_estimate": total_rows_estimate,
                "current_offset": 0,
            }

            if sync_window_start:
                values["sync_window_start"] = sync_window_start
            if sync_window_end:
                values["sync_window_end"] = sync_window_end

            stmt = insert(background_sync_schedule_table).values(
                **values
            ).returning(background_sync_schedule_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            schedule = self._row_to_dict(row)

            logger.info(f"Schedule created: UID={schedule['uid']}")
            return schedule

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create schedule: {e}")
            raise

    async def get_schedule(self, schedule_uid: str | UUID) -> dict[str, Any] | None:
        """
        Get schedule by UID

        Args:
            schedule_uid: Schedule UID

        Returns:
            Schedule record or None if not found
        """
        try:
            stmt = select(background_sync_schedule_table).where(
                background_sync_schedule_table.c.uid == schedule_uid
            )
            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to fetch schedule: {e}")
            raise

    async def get_schedule_by_entity(
        self, entity_name: str
    ) -> dict[str, Any] | None:
        """
        Get schedule by entity name

        Args:
            entity_name: Entity name

        Returns:
            Schedule record or None if not found
        """
        try:
            stmt = select(background_sync_schedule_table).where(
                background_sync_schedule_table.c.entity_name == entity_name
            )
            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to fetch schedule by entity: {e}")
            raise

    async def list_schedules(
        self,
        is_enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List schedules with filters

        Args:
            is_enabled: Filter by enabled status
            limit: Max records to return
            offset: Number of records to skip

        Returns:
            List of schedule records
        """
        try:
            stmt = select(background_sync_schedule_table)

            if is_enabled is not None:
                stmt = stmt.where(
                    background_sync_schedule_table.c.is_enabled == is_enabled
                )

            stmt = stmt.order_by(background_sync_schedule_table.c.entity_name)
            stmt = stmt.limit(limit).offset(offset)

            result = await self.session.execute(stmt)
            rows = result.fetchall()

            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list schedules: {e}")
            raise

    async def get_due_schedules(
        self, current_time: time | None = None
    ) -> list[dict[str, Any]]:
        """
        Get schedules that are due to run (within time window)

        Args:
            current_time: Current time (defaults to now)

        Returns:
            List of due schedules
        """
        try:
            if current_time is None:
                current_time = datetime.now().time()

            stmt = select(background_sync_schedule_table).where(
                background_sync_schedule_table.c.is_enabled == True  # noqa: E712
            )

            result = await self.session.execute(stmt)
            rows = result.fetchall()

            due_schedules = []
            for row in rows:
                schedule = self._row_to_dict(row)
                if self._is_within_time_window(
                    current_time, schedule["sync_window_start"], schedule["sync_window_end"]
                ):
                    due_schedules.append(schedule)

            return due_schedules

        except Exception as e:
            logger.error(f"Failed to get due schedules: {e}")
            raise

    async def update_schedule(
        self,
        schedule_uid: str | UUID,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Update schedule fields

        Args:
            schedule_uid: Schedule UID
            **kwargs: Fields to update

        Returns:
            Updated schedule record

        Raises:
            ValueError: If schedule not found
        """
        logger.debug(f"Updating schedule: UID={schedule_uid}")

        try:
            allowed_fields = {
                "is_enabled", "sync_window_start", "sync_window_end",
                "days_to_complete", "rows_per_day", "total_rows_estimate",
                "current_offset", "last_run_at", "next_run_at"
            }

            values = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not values:
                raise ValueError("No valid fields provided to update")

            stmt = update(background_sync_schedule_table).where(
                background_sync_schedule_table.c.uid == schedule_uid
            ).values(**values).returning(background_sync_schedule_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            if not row:
                raise ValueError(f"Schedule not found: {schedule_uid}")

            return self._row_to_dict(row)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update schedule: {e}")
            raise

    async def update_progress(
        self,
        schedule_uid: str | UUID,
        current_offset: int,
        last_run_at: datetime | None = None,
        next_run_at: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Update schedule progress after a sync run

        Args:
            schedule_uid: Schedule UID
            current_offset: New offset position
            last_run_at: When sync completed (defaults to now)
            next_run_at: When next sync should run

        Returns:
            Updated schedule record
        """
        logger.debug(f"Updating progress: UID={schedule_uid}, offset={current_offset}")

        try:
            values: dict[str, Any] = {
                "current_offset": current_offset,
                "last_run_at": last_run_at or datetime.utcnow(),
            }

            if next_run_at:
                values["next_run_at"] = next_run_at

            stmt = update(background_sync_schedule_table).where(
                background_sync_schedule_table.c.uid == schedule_uid
            ).values(**values).returning(background_sync_schedule_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            if not row:
                raise ValueError(f"Schedule not found: {schedule_uid}")

            return self._row_to_dict(row)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update progress: {e}")
            raise

    async def reset_progress(self, schedule_uid: str | UUID) -> dict[str, Any]:
        """
        Reset schedule progress (for new full sync)

        Args:
            schedule_uid: Schedule UID

        Returns:
            Updated schedule record
        """
        logger.info(f"Resetting progress: UID={schedule_uid}")

        return await self.update_schedule(
            schedule_uid,
            current_offset=0,
        )

    async def delete_schedule(self, schedule_uid: str | UUID) -> bool:
        """
        Delete schedule

        Args:
            schedule_uid: Schedule UID

        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting schedule: UID={schedule_uid}")

        try:
            stmt = delete(background_sync_schedule_table).where(
                background_sync_schedule_table.c.uid == schedule_uid
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete schedule: {e}")
            raise

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get schedule statistics

        Returns:
            Dict with counts and progress info
        """
        try:
            # Total schedules
            total_query = select(func.count()).select_from(background_sync_schedule_table)
            total_result = await self.session.execute(total_query)
            total_schedules = total_result.scalar_one()

            # Enabled schedules
            enabled_query = select(func.count()).select_from(
                background_sync_schedule_table
            ).where(background_sync_schedule_table.c.is_enabled == True)  # noqa: E712
            enabled_result = await self.session.execute(enabled_query)
            enabled_count = enabled_result.scalar_one()

            # Get all schedules for progress calculation
            all_schedules = await self.list_schedules()
            total_progress = 0
            schedules_with_progress = 0

            for schedule in all_schedules:
                if schedule["total_rows_estimate"] and schedule["total_rows_estimate"] > 0:
                    progress = (schedule["current_offset"] / schedule["total_rows_estimate"]) * 100
                    total_progress += progress
                    schedules_with_progress += 1

            avg_progress = total_progress / schedules_with_progress if schedules_with_progress > 0 else 0

            return {
                "total_schedules": total_schedules,
                "enabled_schedules": enabled_count,
                "disabled_schedules": total_schedules - enabled_count,
                "average_progress_percent": round(avg_progress, 2),
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise

    @staticmethod
    def _is_within_time_window(
        current: time, window_start: time, window_end: time
    ) -> bool:
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
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert SQLAlchemy Row to dict"""
        return {
            "uid": str(row.uid),
            "entity_name": row.entity_name,
            "source_system": row.source_system,
            "is_enabled": row.is_enabled,
            "sync_window_start": row.sync_window_start.isoformat() if row.sync_window_start else "19:00:00",
            "sync_window_end": row.sync_window_end.isoformat() if row.sync_window_end else "07:00:00",
            "days_to_complete": row.days_to_complete,
            "rows_per_day": row.rows_per_day,
            "total_rows_estimate": row.total_rows_estimate,
            "current_offset": row.current_offset,
            "last_run_at": row.last_run_at.isoformat() if row.last_run_at else None,
            "next_run_at": row.next_run_at.isoformat() if row.next_run_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
