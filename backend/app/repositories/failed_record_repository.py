"""
Failed Record Repository

Handles failed_records table operations using SQLAlchemy Core.
Dead-letter queue for records that failed processing.
"""

from typing import Any
from uuid import UUID
from loguru import logger
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import failed_records_table
from app.core.uuid_utils import generate_uuid7


class FailedRecordRepository:
    """
    Failed Records Repository

    Manages dead-letter queue for failed records.
    NO ORM - uses SQLAlchemy Core Table API.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository

        Args:
            session: Async database session
        """
        self.session = session

    async def create_failed_record(
        self,
        batch_uid: str | UUID,
        entity_name: str,
        record_data: dict[str, Any],
        error_type: str,
        error_message: str,
        stage: str,
    ) -> dict[str, Any]:
        """
        Create failed record entry

        Args:
            batch_uid: Sync batch UID
            entity_name: Entity name
            record_data: Original record data
            error_type: Type of error (e.g., "validation_error", "insert_error")
            error_message: Detailed error message
            stage: Pipeline stage where error occurred

        Returns:
            Created failed record

        Raises:
            Exception: If creation fails
        """
        logger.debug(
            f"Recording failed record: entity={entity_name}, "
            f"stage={stage}, error={error_type}"
        )

        try:
            uid = generate_uuid7()
            stmt = insert(failed_records_table).values(
                uid=uid,
                batch_uid=batch_uid,
                entity_name=entity_name,
                record_data=record_data,
                error_type=error_type,
                error_message=error_message,
                stage=stage,
                retry_count=0,
            ).returning(failed_records_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            failed_record = self._row_to_dict(row)

            logger.debug(f"Failed record created: UID={failed_record['uid']}")
            return failed_record

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create failed record: {e}")
            raise

    async def get_failed_record(
        self, failed_uid: str | UUID
    ) -> dict[str, Any] | None:
        """
        Get failed record by UID

        Args:
            failed_uid: Failed record UID

        Returns:
            Failed record or None if not found
        """
        try:
            stmt = select(failed_records_table).where(
                failed_records_table.c.uid == failed_uid
            )
            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to fetch failed record: {e}")
            raise

    async def list_failed_records(
        self,
        batch_uid: str | UUID | None = None,
        entity_name: str | None = None,
        error_type: str | None = None,
        stage: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List failed records with filters

        Args:
            batch_uid: Filter by batch
            entity_name: Filter by entity
            error_type: Filter by error type
            stage: Filter by pipeline stage
            limit: Max records to return
            offset: Number of records to skip

        Returns:
            List of failed records
        """
        try:
            stmt = select(failed_records_table)

            if batch_uid:
                stmt = stmt.where(failed_records_table.c.batch_uid == batch_uid)

            if entity_name:
                stmt = stmt.where(failed_records_table.c.entity_name == entity_name)

            if error_type:
                stmt = stmt.where(failed_records_table.c.error_type == error_type)

            if stage:
                stmt = stmt.where(failed_records_table.c.stage == stage)

            stmt = stmt.order_by(failed_records_table.c.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)

            result = await self.session.execute(stmt)
            rows = result.fetchall()

            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list failed records: {e}")
            raise

    async def retry_failed_record(
        self,
        failed_uid: str | UUID,
    ) -> dict[str, Any]:
        """
        Increment retry count for failed record

        Args:
            failed_uid: Failed record UID

        Returns:
            Updated failed record

        Raises:
            Exception: If update fails
        """
        logger.debug(f"Retrying failed record: UID={failed_uid}")

        try:
            from sqlalchemy import func

            stmt = update(failed_records_table).where(
                failed_records_table.c.uid == failed_uid
            ).values(
                retry_count=failed_records_table.c.retry_count + 1,
                last_retry_at=func.now(),
            ).returning(failed_records_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            if not row:
                raise ValueError(f"Failed record not found: {failed_uid}")

            return self._row_to_dict(row)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to retry failed record: {e}")
            raise

    async def resolve_failed_record(
        self,
        failed_uid: str | UUID,
    ) -> None:
        """
        Remove failed record from queue (after successful retry)

        Args:
            failed_uid: Failed record UID

        Raises:
            Exception: If deletion fails
        """
        logger.debug(f"Resolving failed record: UID={failed_uid}")

        try:
            stmt = delete(failed_records_table).where(
                failed_records_table.c.uid == failed_uid
            )
            await self.session.execute(stmt)
            await self.session.commit()

            logger.debug(f"Failed record resolved: {failed_uid}")

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to resolve failed record: {e}")
            raise

    async def get_retryable_records(
        self,
        max_retries: int = 3,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get failed records eligible for retry

        Args:
            max_retries: Maximum retry attempts
            limit: Max records to return

        Returns:
            List of retryable failed records
        """
        try:
            stmt = select(failed_records_table).where(
                failed_records_table.c.retry_count < max_retries
            ).order_by(
                failed_records_table.c.created_at
            ).limit(limit)

            result = await self.session.execute(stmt)
            rows = result.fetchall()

            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get retryable records: {e}")
            raise

    async def delete_old_failed_records(self, days_old: int = 30) -> int:
        """
        Delete old failed records

        Args:
            days_old: Delete records older than this many days

        Returns:
            Number of records deleted
        """
        logger.info(f"Deleting old failed records (>{days_old} days)...")

        try:
            from sqlalchemy import func

            stmt = delete(failed_records_table).where(
                failed_records_table.c.created_at
                < func.now() - func.make_interval(0, 0, 0, days_old)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            deleted_count = result.rowcount

            logger.info(f"Deleted {deleted_count} old failed records")
            return deleted_count

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete old failed records: {e}")
            raise

    async def get_failed_record_statistics(self) -> dict[str, Any]:
        """
        Get failed record statistics

        Returns:
            Dict with counts by error type, stage, and entity

        Example:
            {
                "total_failed": 150,
                "by_error_type": {"validation_error": 100, "insert_error": 50},
                "by_stage": {"normalization": 80, "delta": 40, "ingest": 30},
                "by_entity": {"items": 100, "customers": 50},
                "retryable": 120,
                "max_retry_exceeded": 30
            }
        """
        try:
            from sqlalchemy import func

            # Total failed
            total_query = select(func.count()).select_from(failed_records_table)
            total_result = await self.session.execute(total_query)
            total_failed = total_result.scalar_one()

            # By error type
            by_error_query = select(
                failed_records_table.c.error_type,
                func.count().label("count"),
            ).group_by(failed_records_table.c.error_type)
            by_error_result = await self.session.execute(by_error_query)
            by_error_type = {row.error_type: row.count for row in by_error_result}

            # By stage
            by_stage_query = select(
                failed_records_table.c.stage,
                func.count().label("count"),
            ).group_by(failed_records_table.c.stage)
            by_stage_result = await self.session.execute(by_stage_query)
            by_stage = {row.stage: row.count for row in by_stage_result}

            # By entity
            by_entity_query = select(
                failed_records_table.c.entity_name,
                func.count().label("count"),
            ).group_by(failed_records_table.c.entity_name)
            by_entity_result = await self.session.execute(by_entity_query)
            by_entity = {row.entity_name: row.count for row in by_entity_result}

            # Retryable (retry_count < 3)
            retryable_query = select(func.count()).select_from(
                failed_records_table
            ).where(failed_records_table.c.retry_count < 3)
            retryable_result = await self.session.execute(retryable_query)
            retryable = retryable_result.scalar_one()

            # Max retry exceeded
            max_retry_query = select(func.count()).select_from(
                failed_records_table
            ).where(failed_records_table.c.retry_count >= 3)
            max_retry_result = await self.session.execute(max_retry_query)
            max_retry_exceeded = max_retry_result.scalar_one()

            return {
                "total_failed": total_failed,
                "by_error_type": by_error_type,
                "by_stage": by_stage,
                "by_entity": by_entity,
                "retryable": retryable,
                "max_retry_exceeded": max_retry_exceeded,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert SQLAlchemy Row to dict"""
        return {
            "uid": str(row.uid),
            "batch_uid": str(row.batch_uid),
            "entity_name": row.entity_name,
            "record_data": row.record_data,
            "error_type": row.error_type,
            "error_message": row.error_message,
            "stage": row.stage,
            "retry_count": row.retry_count,
            "last_retry_at": row.last_retry_at.isoformat() if row.last_retry_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
