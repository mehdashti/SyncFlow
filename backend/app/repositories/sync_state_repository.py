"""
Sync State Repository

Handles erp_sync_state table operations using SQLAlchemy Core.
Tracks last sync state per entity for incremental syncs.
"""

from typing import Any
from loguru import logger
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import erp_sync_state_table


class SyncStateRepository:
    """
    ERP Sync State Repository

    Manages sync state tracking for incremental syncs.
    NO ORM - uses SQLAlchemy Core Table API.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository

        Args:
            session: Async database session
        """
        self.session = session

    async def get_sync_state(
        self,
        entity_name: str,
    ) -> dict[str, Any] | None:
        """
        Get sync state for entity

        Args:
            entity_name: Entity name (e.g., "inventory_items")

        Returns:
            Sync state record or None if not found
        """
        try:
            stmt = select(erp_sync_state_table).where(
                erp_sync_state_table.c.entity_name == entity_name
            )
            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to get sync state: {e}")
            raise

    async def create_sync_state(
        self,
        entity_name: str,
        last_sync_rowversion: str | None = None,
        last_sync_timestamp: str | None = None,
    ) -> dict[str, Any]:
        """
        Create sync state for entity

        Args:
            entity_name: Entity name
            last_sync_rowversion: Last synced rowversion
            last_sync_timestamp: Last sync timestamp

        Returns:
            Created sync state record

        Raises:
            Exception: If creation fails
        """
        logger.info(f"Creating sync state for entity: {entity_name}")

        try:
            from sqlalchemy import func

            stmt = insert(erp_sync_state_table).values(
                entity_name=entity_name,
                last_sync_rowversion=last_sync_rowversion,
                last_sync_timestamp=last_sync_timestamp or func.now(),
                last_sync_status="completed",
            ).returning(erp_sync_state_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            sync_state = self._row_to_dict(row)

            logger.info(f"Sync state created: entity={entity_name}")
            return sync_state

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create sync state: {e}")
            raise

    async def update_sync_state(
        self,
        entity_name: str,
        last_sync_rowversion: str | None = None,
        last_sync_timestamp: str | None = None,
        last_sync_status: str = "completed",
        total_records_synced: int | None = None,
    ) -> dict[str, Any]:
        """
        Update sync state for entity

        Args:
            entity_name: Entity name
            last_sync_rowversion: Last synced rowversion
            last_sync_timestamp: Last sync timestamp
            last_sync_status: Sync status ("completed", "failed", "in_progress")
            total_records_synced: Total records synced

        Returns:
            Updated sync state record

        Raises:
            Exception: If update fails
        """
        logger.debug(f"Updating sync state: entity={entity_name}")

        try:
            from sqlalchemy import func

            values: dict[str, Any] = {
                "last_sync_status": last_sync_status,
                "updated_at": func.now(),
            }

            if last_sync_rowversion is not None:
                values["last_sync_rowversion"] = last_sync_rowversion

            if last_sync_timestamp is not None:
                values["last_sync_timestamp"] = last_sync_timestamp
            else:
                values["last_sync_timestamp"] = func.now()

            if total_records_synced is not None:
                values["total_records_synced"] = total_records_synced

            stmt = update(erp_sync_state_table).where(
                erp_sync_state_table.c.entity_name == entity_name
            ).values(**values).returning(erp_sync_state_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            if not row:
                raise ValueError(f"Sync state not found for entity: {entity_name}")

            return self._row_to_dict(row)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update sync state: {e}")
            raise

    async def upsert_sync_state(
        self,
        entity_name: str,
        last_sync_rowversion: str | None = None,
        last_sync_timestamp: str | None = None,
        last_sync_status: str = "completed",
        total_records_synced: int | None = None,
    ) -> dict[str, Any]:
        """
        Create or update sync state (upsert)

        Args:
            entity_name: Entity name
            last_sync_rowversion: Last synced rowversion
            last_sync_timestamp: Last sync timestamp
            last_sync_status: Sync status
            total_records_synced: Total records synced

        Returns:
            Sync state record

        Raises:
            Exception: If operation fails
        """
        existing = await self.get_sync_state(entity_name)

        if existing:
            return await self.update_sync_state(
                entity_name=entity_name,
                last_sync_rowversion=last_sync_rowversion,
                last_sync_timestamp=last_sync_timestamp,
                last_sync_status=last_sync_status,
                total_records_synced=total_records_synced,
            )
        else:
            return await self.create_sync_state(
                entity_name=entity_name,
                last_sync_rowversion=last_sync_rowversion,
                last_sync_timestamp=last_sync_timestamp,
            )

    async def list_all_sync_states(self) -> list[dict[str, Any]]:
        """
        List all sync states

        Returns:
            List of sync state records
        """
        try:
            stmt = select(erp_sync_state_table).order_by(
                erp_sync_state_table.c.entity_name
            )
            result = await self.session.execute(stmt)
            rows = result.fetchall()

            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list sync states: {e}")
            raise

    async def get_entities_needing_sync(
        self,
        hours_since_last_sync: int = 24,
    ) -> list[str]:
        """
        Get entities that need syncing based on time since last sync

        Args:
            hours_since_last_sync: Threshold in hours

        Returns:
            List of entity names needing sync
        """
        try:
            from sqlalchemy import func

            stmt = select(erp_sync_state_table.c.entity_name).where(
                erp_sync_state_table.c.last_sync_timestamp
                < func.now() - func.make_interval(0, 0, 0, 0, hours_since_last_sync)
            )

            result = await self.session.execute(stmt)
            rows = result.fetchall()

            return [row.entity_name for row in rows]

        except Exception as e:
            logger.error(f"Failed to get entities needing sync: {e}")
            raise

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert SQLAlchemy Row to dict"""
        return {
            "entity_name": row.entity_name,
            "last_sync_rowversion": row.last_sync_rowversion,
            "last_sync_timestamp": (
                row.last_sync_timestamp.isoformat()
                if row.last_sync_timestamp
                else None
            ),
            "last_sync_status": row.last_sync_status,
            "total_records_synced": row.total_records_synced,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
