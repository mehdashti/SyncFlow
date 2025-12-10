"""
Parent-Child Resolver Engine

Resolves parent-child dependencies during sync operations.
Queues child records until parent UIDs are available.
"""

from typing import Any
from loguru import logger
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import pending_children_table
from app.core.config import settings


class ParentChildResolver:
    """
    Parent-Child Dependency Resolver

    Problem:
    - Child records reference parent UIDs (foreign keys)
    - If parent not synced yet, child insert fails
    - Need to queue children until parent is available

    Solution:
    - Detect missing parent references
    - Store pending children in queue table
    - Retry after parent sync completes
    - Track retry attempts and failures

    Example:
    - Sales Order Line (child) references Sales Order (parent)
    - If parent order not synced, queue the line
    - After parent synced, retry line insertion with parent UID
    """

    def __init__(
        self,
        session: AsyncSession,
        max_retries: int = 3,
    ):
        """
        Initialize resolver

        Args:
            session: Database session
            max_retries: Maximum retry attempts for pending children
        """
        self.session = session
        self.max_retries = max_retries

        logger.info(f"Parent-Child Resolver initialized (max_retries={max_retries})")

    async def detect_missing_parent(
        self,
        child_record: dict[str, Any],
        parent_entity: str,
        parent_bk_hash_field: str,
    ) -> str | None:
        """
        Detect if child record has missing parent reference

        Args:
            child_record: Child record data
            parent_entity: Parent entity name (e.g., "sales_orders")
            parent_bk_hash_field: Field containing parent BK_HASH

        Returns:
            Parent BK_HASH if missing, None if parent exists or not required

        Example:
            child_record = {"order_line_number": "001", "order_bk_hash": "abc123..."}
            parent_bk_hash = await resolver.detect_missing_parent(
                child_record,
                parent_entity="sales_orders",
                parent_bk_hash_field="order_bk_hash"
            )
            if parent_bk_hash:
                # Parent missing, queue child
        """
        parent_bk_hash = child_record.get(parent_bk_hash_field)

        if not parent_bk_hash:
            # No parent reference, not a child record
            return None

        # TODO: Query ScheduleHub to check if parent exists
        # For now, assume parent might be missing
        # In real implementation, use ScheduleHubClient.get_by_bk_hash()

        logger.debug(
            f"Checking parent existence: "
            f"entity={parent_entity}, bk_hash={parent_bk_hash[:16]}..."
        )

        # Placeholder: return None (parent exists)
        # Real implementation will query ScheduleHub
        return None

    async def queue_pending_child(
        self,
        batch_uid: str,
        entity_name: str,
        child_record: dict[str, Any],
        parent_entity: str,
        parent_bk_hash: str,
        reason: str = "Parent not synced",
    ) -> str:
        """
        Queue child record until parent is available

        Args:
            batch_uid: Current sync batch UID
            entity_name: Child entity name
            child_record: Child record data (with identity fields)
            parent_entity: Parent entity name
            parent_bk_hash: Parent BK_HASH that's missing
            reason: Reason for queuing

        Returns:
            UID of queued pending child record

        Raises:
            Exception: If queue insertion fails
        """
        child_bk_hash = child_record.get("erp_key_hash")
        child_ref = child_record.get("erp_ref_str", "N/A")

        logger.info(
            f"Queuing pending child: {entity_name} {child_ref} "
            f"(waiting for {parent_entity})"
        )

        try:
            stmt = insert(pending_children_table).values(
                batch_uid=batch_uid,
                entity_name=entity_name,
                child_bk_hash=child_bk_hash,
                child_data=child_record,
                parent_entity=parent_entity,
                parent_bk_hash=parent_bk_hash,
                retry_count=0,
                reason=reason,
            ).returning(pending_children_table.c.uid)

            result = await self.session.execute(stmt)
            await self.session.commit()

            pending_uid = result.scalar_one()

            logger.debug(f"Child queued: UID={pending_uid}")
            return str(pending_uid)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to queue pending child: {e}")
            raise

    async def get_pending_children(
        self,
        parent_entity: str,
        parent_bk_hash: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get pending children waiting for specific parent

        Args:
            parent_entity: Parent entity name
            parent_bk_hash: Optional specific parent BK_HASH
            limit: Maximum records to fetch

        Returns:
            List of pending child records

        Example:
            # After syncing parent "sales_orders"
            pending = await resolver.get_pending_children(
                parent_entity="sales_orders",
                limit=1000
            )
            # Retry all pending children for this parent
        """
        logger.info(f"Fetching pending children for parent: {parent_entity}")

        try:
            query = select(pending_children_table).where(
                pending_children_table.c.parent_entity == parent_entity,
                pending_children_table.c.retry_count < self.max_retries,
            )

            if parent_bk_hash:
                query = query.where(
                    pending_children_table.c.parent_bk_hash == parent_bk_hash
                )

            query = query.limit(limit).order_by(pending_children_table.c.created_at)

            result = await self.session.execute(query)
            rows = result.fetchall()

            pending_records = []
            for row in rows:
                pending_records.append({
                    "uid": str(row.uid),
                    "entity_name": row.entity_name,
                    "child_bk_hash": row.child_bk_hash,
                    "child_data": row.child_data,
                    "parent_entity": row.parent_entity,
                    "parent_bk_hash": row.parent_bk_hash,
                    "retry_count": row.retry_count,
                    "reason": row.reason,
                    "created_at": row.created_at,
                })

            logger.info(f"Found {len(pending_records)} pending children")
            return pending_records

        except Exception as e:
            logger.error(f"Failed to fetch pending children: {e}")
            raise

    async def retry_pending_child(
        self,
        pending_uid: str,
        parent_uid: str | None = None,
    ) -> dict[str, Any]:
        """
        Retry syncing a pending child record

        Args:
            pending_uid: Pending child record UID
            parent_uid: Parent UID (if now available)

        Returns:
            Updated pending child record

        Raises:
            Exception: If retry fails
        """
        logger.debug(f"Retrying pending child: UID={pending_uid}")

        try:
            # Fetch pending record
            query = select(pending_children_table).where(
                pending_children_table.c.uid == pending_uid
            )
            result = await self.session.execute(query)
            row = result.fetchone()

            if not row:
                raise ValueError(f"Pending child not found: {pending_uid}")

            child_data = row.child_data
            retry_count = row.retry_count

            # If parent UID available, update child data
            if parent_uid:
                # TODO: Update child_data with parent_uid in appropriate field
                # This depends on field mapping configuration
                pass

            # TODO: Attempt to sync child with ScheduleHubClient
            # If successful, delete from pending queue
            # If failed, increment retry_count

            # For now, just increment retry count
            from sqlalchemy import update
            stmt = update(pending_children_table).where(
                pending_children_table.c.uid == pending_uid
            ).values(
                retry_count=retry_count + 1,
                last_retry_at=lambda: "NOW()",
            ).returning(pending_children_table.c.retry_count)

            result = await self.session.execute(stmt)
            await self.session.commit()

            new_retry_count = result.scalar_one()

            logger.debug(
                f"Pending child retry incremented: "
                f"UID={pending_uid}, retries={new_retry_count}"
            )

            return {
                "uid": pending_uid,
                "retry_count": new_retry_count,
                "status": "retried",
            }

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to retry pending child: {e}")
            raise

    async def resolve_pending_child(
        self,
        pending_uid: str,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        """
        Resolve pending child (remove from queue or mark as failed)

        Args:
            pending_uid: Pending child UID
            success: Whether child sync succeeded
            error_message: Optional error message if failed

        Raises:
            Exception: If resolution fails
        """
        if success:
            logger.info(f"Resolving pending child (success): UID={pending_uid}")

            try:
                # Remove from pending queue
                stmt = delete(pending_children_table).where(
                    pending_children_table.c.uid == pending_uid
                )
                await self.session.execute(stmt)
                await self.session.commit()

                logger.debug(f"Pending child removed from queue: {pending_uid}")

            except Exception as e:
                await self.session.rollback()
                logger.error(f"Failed to remove pending child: {e}")
                raise

        else:
            logger.warning(
                f"Pending child failed: UID={pending_uid}, error={error_message}"
            )

            # Check if max retries exceeded
            query = select(pending_children_table.c.retry_count).where(
                pending_children_table.c.uid == pending_uid
            )
            result = await self.session.execute(query)
            retry_count = result.scalar_one_or_none()

            if retry_count and retry_count >= self.max_retries:
                # Move to failed_records table
                logger.error(
                    f"Max retries exceeded for pending child: {pending_uid}, "
                    f"moving to failed_records"
                )

                # TODO: Move to failed_records table with FailedRecordRepository
                # Then delete from pending_children

                # For now, just delete
                stmt = delete(pending_children_table).where(
                    pending_children_table.c.uid == pending_uid
                )
                await self.session.execute(stmt)
                await self.session.commit()

    async def get_pending_statistics(self) -> dict[str, Any]:
        """
        Get statistics about pending children

        Returns:
            Dict with counts by entity and parent

        Example:
            {
                "total_pending": 150,
                "by_parent": {
                    "sales_orders": 100,
                    "customers": 50
                },
                "by_entity": {
                    "sales_order_lines": 100,
                    "contact_persons": 50
                },
                "max_retry_exceeded": 5
            }
        """
        logger.debug("Calculating pending children statistics...")

        try:
            from sqlalchemy import func

            # Total pending
            total_query = select(func.count()).select_from(pending_children_table)
            total_result = await self.session.execute(total_query)
            total_pending = total_result.scalar_one()

            # By parent entity
            by_parent_query = select(
                pending_children_table.c.parent_entity,
                func.count().label("count"),
            ).group_by(pending_children_table.c.parent_entity)
            by_parent_result = await self.session.execute(by_parent_query)
            by_parent = {row.parent_entity: row.count for row in by_parent_result}

            # By child entity
            by_entity_query = select(
                pending_children_table.c.entity_name,
                func.count().label("count"),
            ).group_by(pending_children_table.c.entity_name)
            by_entity_result = await self.session.execute(by_entity_query)
            by_entity = {row.entity_name: row.count for row in by_entity_result}

            # Max retry exceeded
            max_retry_query = select(func.count()).select_from(
                pending_children_table
            ).where(pending_children_table.c.retry_count >= self.max_retries)
            max_retry_result = await self.session.execute(max_retry_query)
            max_retry_exceeded = max_retry_result.scalar_one()

            stats = {
                "total_pending": total_pending,
                "by_parent": by_parent,
                "by_entity": by_entity,
                "max_retry_exceeded": max_retry_exceeded,
            }

            logger.info(
                f"Pending statistics: total={total_pending}, "
                f"max_retry_exceeded={max_retry_exceeded}"
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
            raise

    async def cleanup_resolved_children(self, days_old: int = 7) -> int:
        """
        Cleanup old resolved children from queue

        Args:
            days_old: Remove records older than this many days

        Returns:
            Number of records deleted

        Note:
            This is a safety cleanup for records that were resolved
            but not properly deleted from queue
        """
        logger.info(f"Cleaning up old pending children (>{days_old} days)...")

        try:
            from sqlalchemy import func

            stmt = delete(pending_children_table).where(
                pending_children_table.c.created_at
                < func.now() - func.make_interval(0, 0, 0, days_old)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            deleted_count = result.rowcount

            logger.info(f"Cleaned up {deleted_count} old pending children")
            return deleted_count

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Cleanup failed: {e}")
            raise


# Convenience functions

async def queue_child_for_parent(
    session: AsyncSession,
    batch_uid: str,
    entity_name: str,
    child_record: dict[str, Any],
    parent_entity: str,
    parent_bk_hash: str,
) -> str:
    """
    Convenience function to queue pending child

    Args:
        session: Database session
        batch_uid: Sync batch UID
        entity_name: Child entity name
        child_record: Child record data
        parent_entity: Parent entity name
        parent_bk_hash: Parent BK_HASH

    Returns:
        UID of queued record
    """
    resolver = ParentChildResolver(session)
    return await resolver.queue_pending_child(
        batch_uid=batch_uid,
        entity_name=entity_name,
        child_record=child_record,
        parent_entity=parent_entity,
        parent_bk_hash=parent_bk_hash,
    )


async def retry_children_for_parent(
    session: AsyncSession,
    parent_entity: str,
    parent_bk_hash: str | None = None,
) -> list[dict[str, Any]]:
    """
    Convenience function to get and retry pending children

    Args:
        session: Database session
        parent_entity: Parent entity name
        parent_bk_hash: Optional specific parent BK_HASH

    Returns:
        List of pending children to retry
    """
    resolver = ParentChildResolver(session)
    return await resolver.get_pending_children(
        parent_entity=parent_entity,
        parent_bk_hash=parent_bk_hash,
    )
