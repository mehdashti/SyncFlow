"""
Batch Repository

Handles sync_batches table operations using SQLAlchemy Core.
Tracks sync operations with metrics and status.
"""

from typing import Any
from uuid import UUID
from loguru import logger
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import sync_batches_table
from app.core.config import settings
from app.core.uuid_utils import generate_uuid7


class BatchRepository:
    """
    Sync Batches Repository

    Manages sync batch records using SQLAlchemy Core.
    NO ORM - uses Table API for all operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository

        Args:
            session: Async database session
        """
        self.session = session

    async def create_batch(
        self,
        entity_name: str,
        sync_type: str,
        total_records: int = 0,
        connector_api_slug: str | None = None,
    ) -> dict[str, Any]:
        """
        Create new sync batch

        Args:
            entity_name: Entity being synced (e.g., "inventory_items")
            sync_type: Type of sync ("full", "incremental", "background")
            total_records: Total records to sync
            connector_api_slug: APISmith API slug

        Returns:
            Created batch record

        Raises:
            Exception: If creation fails
        """
        logger.info(
            f"Creating sync batch: entity={entity_name}, type={sync_type}, "
            f"records={total_records}"
        )

        try:
            uid = generate_uuid7()
            stmt = insert(sync_batches_table).values(
                uid=uid,
                entity_name=entity_name,
                sync_type=sync_type,
                status="pending",
                total_records=total_records,
                connector_api_slug=connector_api_slug,
            ).returning(sync_batches_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            batch = self._row_to_dict(row)

            logger.info(f"Batch created: UID={batch['uid']}")
            return batch

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create batch: {e}")
            raise

    async def get_batch(self, batch_uid: str | UUID) -> dict[str, Any] | None:
        """
        Get batch by UID

        Args:
            batch_uid: Batch UID

        Returns:
            Batch record or None if not found
        """
        try:
            stmt = select(sync_batches_table).where(
                sync_batches_table.c.uid == batch_uid
            )
            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to fetch batch: {e}")
            raise

    async def update_batch_status(
        self,
        batch_uid: str | UUID,
        status: str,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Update batch status

        Args:
            batch_uid: Batch UID
            status: New status ("pending", "running", "completed", "failed")
            error_message: Optional error message if failed

        Returns:
            Updated batch record

        Raises:
            Exception: If update fails
        """
        logger.debug(f"Updating batch status: UID={batch_uid}, status={status}")

        try:
            values: dict[str, Any] = {"status": status}

            if error_message:
                values["error_message"] = error_message

            if status == "running":
                from sqlalchemy import func
                values["started_at"] = func.now()
            elif status in ("completed", "failed"):
                from sqlalchemy import func
                values["completed_at"] = func.now()

            stmt = update(sync_batches_table).where(
                sync_batches_table.c.uid == batch_uid
            ).values(**values).returning(sync_batches_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            if not row:
                raise ValueError(f"Batch not found: {batch_uid}")

            return self._row_to_dict(row)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update batch status: {e}")
            raise

    async def update_batch_metrics(
        self,
        batch_uid: str | UUID,
        processed: int | None = None,
        inserted: int | None = None,
        updated: int | None = None,
        deleted: int | None = None,
        skipped: int | None = None,
        failed: int | None = None,
    ) -> dict[str, Any]:
        """
        Update batch metrics

        Args:
            batch_uid: Batch UID
            processed: Records processed
            inserted: Records inserted
            updated: Records updated
            deleted: Records deleted
            skipped: Records skipped
            failed: Records failed

        Returns:
            Updated batch record

        Raises:
            Exception: If update fails
        """
        logger.debug(f"Updating batch metrics: UID={batch_uid}")

        try:
            values: dict[str, Any] = {}

            if processed is not None:
                values["records_processed"] = processed
            if inserted is not None:
                values["records_inserted"] = inserted
            if updated is not None:
                values["records_updated"] = updated
            if deleted is not None:
                values["records_deleted"] = deleted
            if skipped is not None:
                values["records_skipped"] = skipped
            if failed is not None:
                values["records_failed"] = failed

            if not values:
                raise ValueError("No metrics provided to update")

            stmt = update(sync_batches_table).where(
                sync_batches_table.c.uid == batch_uid
            ).values(**values).returning(sync_batches_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            if not row:
                raise ValueError(f"Batch not found: {batch_uid}")

            return self._row_to_dict(row)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update batch metrics: {e}")
            raise

    async def list_batches(
        self,
        entity_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List sync batches with filters

        Args:
            entity_name: Filter by entity
            status: Filter by status
            limit: Max records to return
            offset: Number of records to skip

        Returns:
            List of batch records
        """
        try:
            stmt = select(sync_batches_table)

            if entity_name:
                stmt = stmt.where(sync_batches_table.c.entity_name == entity_name)

            if status:
                stmt = stmt.where(sync_batches_table.c.status == status)

            stmt = stmt.order_by(sync_batches_table.c.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)

            result = await self.session.execute(stmt)
            rows = result.fetchall()

            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list batches: {e}")
            raise

    async def get_latest_batch(
        self,
        entity_name: str,
        sync_type: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Get latest batch for entity

        Args:
            entity_name: Entity name
            sync_type: Optional sync type filter

        Returns:
            Latest batch record or None
        """
        try:
            stmt = select(sync_batches_table).where(
                sync_batches_table.c.entity_name == entity_name
            )

            if sync_type:
                stmt = stmt.where(sync_batches_table.c.sync_type == sync_type)

            stmt = stmt.order_by(sync_batches_table.c.created_at.desc()).limit(1)

            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to get latest batch: {e}")
            raise

    async def delete_old_batches(self, days_old: int = 30) -> int:
        """
        Delete old completed batches

        Args:
            days_old: Delete batches older than this many days

        Returns:
            Number of batches deleted
        """
        logger.info(f"Deleting old batches (>{days_old} days)...")

        try:
            from sqlalchemy import func

            stmt = delete(sync_batches_table).where(
                sync_batches_table.c.status == "completed",
                sync_batches_table.c.completed_at
                < func.now() - func.make_interval(0, 0, 0, days_old)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            deleted_count = result.rowcount

            logger.info(f"Deleted {deleted_count} old batches")
            return deleted_count

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete old batches: {e}")
            raise

    async def get_batch_statistics(self) -> dict[str, Any]:
        """
        Get batch statistics

        Returns:
            Dict with counts by status and entity

        Example:
            {
                "total_batches": 1000,
                "by_status": {"completed": 800, "failed": 50, "running": 10},
                "by_entity": {"inventory_items": 500, "customers": 300}
            }
        """
        try:
            from sqlalchemy import func

            # Total batches
            total_query = select(func.count()).select_from(sync_batches_table)
            total_result = await self.session.execute(total_query)
            total_batches = total_result.scalar_one()

            # By status
            by_status_query = select(
                sync_batches_table.c.status,
                func.count().label("count"),
            ).group_by(sync_batches_table.c.status)
            by_status_result = await self.session.execute(by_status_query)
            by_status = {row.status: row.count for row in by_status_result}

            # By entity
            by_entity_query = select(
                sync_batches_table.c.entity_name,
                func.count().label("count"),
            ).group_by(sync_batches_table.c.entity_name)
            by_entity_result = await self.session.execute(by_entity_query)
            by_entity = {row.entity_name: row.count for row in by_entity_result}

            return {
                "total_batches": total_batches,
                "by_status": by_status,
                "by_entity": by_entity,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert SQLAlchemy Row to dict"""
        return {
            "uid": str(row.uid),
            "entity_name": row.entity_name,
            "sync_type": row.sync_type,
            "status": row.status,
            "total_records": row.total_records,
            "records_processed": row.records_processed,
            "records_inserted": row.records_inserted,
            "records_updated": row.records_updated,
            "records_deleted": row.records_deleted,
            "records_skipped": row.records_skipped,
            "records_failed": row.records_failed,
            "connector_api_slug": row.connector_api_slug,
            "last_rowversion": row.last_rowversion,
            "error_message": row.error_message,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
