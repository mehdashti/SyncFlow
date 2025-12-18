"""
Entity Config Repository

Handles entity_config table operations using SQLAlchemy Core.
Manages entity configurations including business keys and parent references.
"""

from typing import Any
from uuid import UUID
from loguru import logger
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import entity_config_table, sync_batches_table, field_mappings_table
from app.core.uuid_utils import generate_uuid7


class EntityConfigRepository:
    """
    Entity Configuration Repository

    Manages entity configurations for SyncFlow.
    NO ORM - uses SQLAlchemy Core Table API.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository

        Args:
            session: Async database session
        """
        self.session = session

    async def create_entity(
        self,
        entity_name: str,
        connector_api_slug: str,
        business_key_fields: list[str],
        sync_enabled: bool = True,
        sync_schedule: str | None = None,
        parent_refs_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create entity configuration

        Args:
            entity_name: Entity name (unique)
            connector_api_slug: APISmith API slug
            business_key_fields: List of business key field names
            sync_enabled: Enable automatic sync
            sync_schedule: Cron expression for scheduled sync
            parent_refs_config: Parent references config for FK resolution

        Returns:
            Created entity config record

        Raises:
            Exception: If creation fails
        """
        logger.info(f"Creating entity config: {entity_name}")

        try:
            uid = generate_uuid7()
            stmt = insert(entity_config_table).values(
                uid=uid,
                entity_name=entity_name,
                connector_api_slug=connector_api_slug,
                business_key_fields=business_key_fields,
                sync_enabled=sync_enabled,
                sync_schedule=sync_schedule,
                parent_refs_config=parent_refs_config,
            ).returning(entity_config_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            entity = self._row_to_dict(row)

            logger.info(f"Entity config created: {entity_name}")
            return entity

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create entity config: {e}")
            raise

    async def get_entity(
        self, entity_name: str
    ) -> dict[str, Any] | None:
        """
        Get entity configuration by name

        Args:
            entity_name: Entity name

        Returns:
            Entity config record or None if not found
        """
        try:
            stmt = select(entity_config_table).where(
                entity_config_table.c.entity_name == entity_name
            )
            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to fetch entity config: {e}")
            raise

    async def get_entity_by_uid(
        self, uid: str | UUID
    ) -> dict[str, Any] | None:
        """
        Get entity configuration by UID

        Args:
            uid: Entity config UID

        Returns:
            Entity config record or None if not found
        """
        try:
            stmt = select(entity_config_table).where(
                entity_config_table.c.uid == uid
            )
            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to fetch entity config: {e}")
            raise

    async def list_entities(
        self,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
        sync_enabled: bool | None = None,
    ) -> dict[str, Any]:
        """
        List entity configurations with pagination

        Args:
            page: Page number (1-based)
            page_size: Items per page
            search: Search by entity name
            sync_enabled: Filter by sync_enabled

        Returns:
            Paginated list with items, total, page, page_size, total_pages
        """
        try:
            # Base query
            query = select(entity_config_table)
            count_query = select(func.count()).select_from(entity_config_table)

            # Apply filters
            if search:
                query = query.where(
                    entity_config_table.c.entity_name.ilike(f"%{search}%")
                )
                count_query = count_query.where(
                    entity_config_table.c.entity_name.ilike(f"%{search}%")
                )

            if sync_enabled is not None:
                query = query.where(
                    entity_config_table.c.sync_enabled == sync_enabled
                )
                count_query = count_query.where(
                    entity_config_table.c.sync_enabled == sync_enabled
                )

            # Get total count
            total_result = await self.session.execute(count_query)
            total = total_result.scalar() or 0

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.order_by(entity_config_table.c.entity_name)
            query = query.offset(offset).limit(page_size)

            result = await self.session.execute(query)
            rows = result.fetchall()

            items = [self._row_to_dict(row) for row in rows]
            total_pages = (total + page_size - 1) // page_size

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }

        except Exception as e:
            logger.error(f"Failed to list entity configs: {e}")
            raise

    async def update_entity(
        self,
        entity_name: str,
        connector_api_slug: str | None = None,
        business_key_fields: list[str] | None = None,
        sync_enabled: bool | None = None,
        sync_schedule: str | None = None,
        parent_refs_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Update entity configuration

        Args:
            entity_name: Entity name to update
            connector_api_slug: New connector API slug
            business_key_fields: New business key fields
            sync_enabled: New sync_enabled value
            sync_schedule: New sync schedule
            parent_refs_config: New parent refs config

        Returns:
            Updated entity config record

        Raises:
            ValueError: If entity not found
            Exception: If update fails
        """
        logger.info(f"Updating entity config: {entity_name}")

        try:
            values: dict[str, Any] = {}

            if connector_api_slug is not None:
                values["connector_api_slug"] = connector_api_slug

            if business_key_fields is not None:
                values["business_key_fields"] = business_key_fields

            if sync_enabled is not None:
                values["sync_enabled"] = sync_enabled

            if sync_schedule is not None:
                values["sync_schedule"] = sync_schedule

            if parent_refs_config is not None:
                values["parent_refs_config"] = parent_refs_config

            if not values:
                # No changes, just return current entity
                entity = await self.get_entity(entity_name)
                if not entity:
                    raise ValueError(f"Entity not found: {entity_name}")
                return entity

            stmt = update(entity_config_table).where(
                entity_config_table.c.entity_name == entity_name
            ).values(**values).returning(entity_config_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            if not row:
                raise ValueError(f"Entity not found: {entity_name}")

            return self._row_to_dict(row)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update entity config: {e}")
            raise

    async def delete_entity(
        self,
        entity_name: str,
    ) -> bool:
        """
        Delete entity configuration

        Also deletes associated field mappings.

        Args:
            entity_name: Entity name to delete

        Returns:
            True if deleted, False if not found

        Raises:
            Exception: If deletion fails
        """
        logger.info(f"Deleting entity config: {entity_name}")

        try:
            # First delete field mappings
            delete_mappings_stmt = delete(field_mappings_table).where(
                field_mappings_table.c.entity_name == entity_name
            )
            await self.session.execute(delete_mappings_stmt)

            # Then delete entity config
            stmt = delete(entity_config_table).where(
                entity_config_table.c.entity_name == entity_name
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            deleted = result.rowcount > 0

            if deleted:
                logger.info(f"Entity config deleted: {entity_name}")
            else:
                logger.warning(f"Entity config not found: {entity_name}")

            return deleted

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete entity config: {e}")
            raise

    async def get_entity_with_stats(
        self, entity_name: str
    ) -> dict[str, Any] | None:
        """
        Get entity configuration with sync statistics

        Args:
            entity_name: Entity name

        Returns:
            Entity config with sync_stats or None if not found
        """
        try:
            # Get entity config
            entity = await self.get_entity(entity_name)
            if not entity:
                return None

            # Get sync stats
            stats_stmt = select(
                func.count().label("total_syncs"),
                func.sum(
                    func.cast(sync_batches_table.c.status == "completed", Integer)
                ).label("successful_syncs"),
                func.sum(
                    func.cast(sync_batches_table.c.status == "failed", Integer)
                ).label("failed_syncs"),
                func.max(sync_batches_table.c.started_at).label("last_sync_at"),
                func.sum(sync_batches_table.c.rows_inserted + sync_batches_table.c.rows_updated).label("total_records_synced"),
            ).where(
                sync_batches_table.c.entity_name == entity_name
            )

            stats_result = await self.session.execute(stats_stmt)
            stats_row = stats_result.fetchone()

            # Get last sync status
            last_sync_stmt = select(
                sync_batches_table.c.status
            ).where(
                sync_batches_table.c.entity_name == entity_name
            ).order_by(
                sync_batches_table.c.started_at.desc()
            ).limit(1)

            last_sync_result = await self.session.execute(last_sync_stmt)
            last_sync_row = last_sync_result.fetchone()

            entity["sync_stats"] = {
                "total_syncs": stats_row.total_syncs or 0,
                "successful_syncs": stats_row.successful_syncs or 0,
                "failed_syncs": stats_row.failed_syncs or 0,
                "last_sync_at": stats_row.last_sync_at.isoformat() if stats_row.last_sync_at else None,
                "last_sync_status": last_sync_row.status if last_sync_row else None,
                "total_records_synced": stats_row.total_records_synced or 0,
            }

            return entity

        except Exception as e:
            logger.error(f"Failed to fetch entity with stats: {e}")
            raise

    async def list_entities_with_stats(
        self,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
    ) -> dict[str, Any]:
        """
        List entities with basic sync stats

        Args:
            page: Page number
            page_size: Items per page
            search: Search by entity name

        Returns:
            Paginated list with basic stats
        """
        try:
            # Get basic list
            result = await self.list_entities(page, page_size, search)

            # Enrich with stats for each entity
            enriched_items = []
            for item in result["items"]:
                # Get last sync info
                last_sync_stmt = select(
                    sync_batches_table.c.status,
                    sync_batches_table.c.started_at,
                    func.count().over().label("total_syncs"),
                ).where(
                    sync_batches_table.c.entity_name == item["entity_name"]
                ).order_by(
                    sync_batches_table.c.started_at.desc()
                ).limit(1)

                last_sync_result = await self.session.execute(last_sync_stmt)
                last_sync_row = last_sync_result.fetchone()

                # Count total syncs
                count_stmt = select(func.count()).select_from(
                    sync_batches_table
                ).where(
                    sync_batches_table.c.entity_name == item["entity_name"]
                )
                count_result = await self.session.execute(count_stmt)
                total_syncs = count_result.scalar() or 0

                enriched_items.append({
                    "entity_name": item["entity_name"],
                    "connector_api_slug": item["connector_api_slug"],
                    "sync_enabled": item["sync_enabled"],
                    "total_syncs": total_syncs,
                    "last_sync_at": last_sync_row.started_at.isoformat() if last_sync_row and last_sync_row.started_at else None,
                    "last_sync_status": last_sync_row.status if last_sync_row else None,
                })

            result["items"] = enriched_items
            return result

        except Exception as e:
            logger.error(f"Failed to list entities with stats: {e}")
            raise

    async def entity_exists(self, entity_name: str) -> bool:
        """
        Check if entity exists

        Args:
            entity_name: Entity name

        Returns:
            True if entity exists
        """
        try:
            stmt = select(func.count()).select_from(
                entity_config_table
            ).where(
                entity_config_table.c.entity_name == entity_name
            )
            result = await self.session.execute(stmt)
            count = result.scalar() or 0
            return count > 0

        except Exception as e:
            logger.error(f"Failed to check entity existence: {e}")
            raise

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert SQLAlchemy Row to dict"""
        return {
            "uid": str(row.uid),
            "entity_name": row.entity_name,
            "connector_api_slug": row.connector_api_slug,
            "business_key_fields": row.business_key_fields,
            "sync_enabled": row.sync_enabled,
            "sync_schedule": row.sync_schedule,
            "parent_refs_config": row.parent_refs_config,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
