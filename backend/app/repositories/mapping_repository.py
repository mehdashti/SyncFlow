"""
Mapping Repository

Handles field_mappings table operations using SQLAlchemy Core.
Manages source→target field mappings for normalization.
"""

from typing import Any
from uuid import UUID
from loguru import logger
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import field_mappings_table
from app.core.uuid_utils import generate_uuid7


class MappingRepository:
    """
    Field Mappings Repository

    Manages field mapping configurations for entities.
    NO ORM - uses SQLAlchemy Core Table API.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository

        Args:
            session: Async database session
        """
        self.session = session

    async def create_mapping(
        self,
        entity_name: str,
        source_field: str,
        target_field: str,
        transformation: str | None = None,
        is_required: bool = False,
    ) -> dict[str, Any]:
        """
        Create field mapping

        Args:
            entity_name: Entity name
            source_field: Source field name (from APISmith)
            target_field: Target field name (in ScheduleHub)
            transformation: Optional transformation (uppercase, lowercase, etc.)
            is_required: Whether field is required

        Returns:
            Created mapping record

        Raises:
            Exception: If creation fails
        """
        logger.debug(
            f"Creating field mapping: {entity_name}.{source_field} → {target_field}"
        )

        try:
            uid = generate_uuid7()
            stmt = insert(field_mappings_table).values(
                uid=uid,
                entity_name=entity_name,
                source_field=source_field,
                target_field=target_field,
                transformation=transformation,
                is_required=is_required,
            ).returning(field_mappings_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            mapping = self._row_to_dict(row)

            logger.debug(f"Mapping created: UID={mapping['uid']}")
            return mapping

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create mapping: {e}")
            raise

    async def get_mapping(
        self, mapping_uid: str | UUID
    ) -> dict[str, Any] | None:
        """
        Get mapping by UID

        Args:
            mapping_uid: Mapping UID

        Returns:
            Mapping record or None if not found
        """
        try:
            stmt = select(field_mappings_table).where(
                field_mappings_table.c.uid == mapping_uid
            )
            result = await self.session.execute(stmt)
            row = result.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to fetch mapping: {e}")
            raise

    async def get_mappings_for_entity(
        self,
        entity_name: str,
    ) -> list[dict[str, Any]]:
        """
        Get all mappings for entity

        Args:
            entity_name: Entity name

        Returns:
            List of mapping records for entity
        """
        try:
            stmt = select(field_mappings_table).where(
                field_mappings_table.c.entity_name == entity_name
            ).order_by(field_mappings_table.c.source_field)

            result = await self.session.execute(stmt)
            rows = result.fetchall()

            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to fetch mappings for entity: {e}")
            raise

    async def update_mapping(
        self,
        mapping_uid: str | UUID,
        target_field: str | None = None,
        transformation: str | None = None,
        is_required: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update field mapping

        Args:
            mapping_uid: Mapping UID
            target_field: New target field name
            transformation: New transformation
            is_required: New is_required value

        Returns:
            Updated mapping record

        Raises:
            Exception: If update fails
        """
        logger.debug(f"Updating mapping: UID={mapping_uid}")

        try:
            values: dict[str, Any] = {}

            if target_field is not None:
                values["target_field"] = target_field

            if transformation is not None:
                values["transformation"] = transformation

            if is_required is not None:
                values["is_required"] = is_required

            if not values:
                raise ValueError("No values provided to update")

            stmt = update(field_mappings_table).where(
                field_mappings_table.c.uid == mapping_uid
            ).values(**values).returning(field_mappings_table)

            result = await self.session.execute(stmt)
            await self.session.commit()

            row = result.fetchone()
            if not row:
                raise ValueError(f"Mapping not found: {mapping_uid}")

            return self._row_to_dict(row)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update mapping: {e}")
            raise

    async def delete_mapping(
        self,
        mapping_uid: str | UUID,
    ) -> None:
        """
        Delete field mapping

        Args:
            mapping_uid: Mapping UID

        Raises:
            Exception: If deletion fails
        """
        logger.debug(f"Deleting mapping: UID={mapping_uid}")

        try:
            stmt = delete(field_mappings_table).where(
                field_mappings_table.c.uid == mapping_uid
            )
            await self.session.execute(stmt)
            await self.session.commit()

            logger.debug(f"Mapping deleted: {mapping_uid}")

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete mapping: {e}")
            raise

    async def bulk_create_mappings(
        self,
        entity_name: str,
        mappings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Bulk create mappings for entity

        Args:
            entity_name: Entity name
            mappings: List of mapping dicts with source_field, target_field, etc.

        Returns:
            List of created mapping records

        Raises:
            Exception: If bulk creation fails

        Example:
            mappings = [
                {"source_field": "ITEM_NO", "target_field": "item_number"},
                {"source_field": "DESCRIPTION", "target_field": "description"},
            ]
        """
        logger.info(f"Bulk creating {len(mappings)} mappings for {entity_name}")

        try:
            values_list = []
            for mapping in mappings:
                values_list.append({
                    "entity_name": entity_name,
                    "source_field": mapping["source_field"],
                    "target_field": mapping["target_field"],
                    "transformation": mapping.get("transformation"),
                    "is_required": mapping.get("is_required", False),
                })

            stmt = insert(field_mappings_table).values(values_list).returning(
                field_mappings_table
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            rows = result.fetchall()
            created = [self._row_to_dict(row) for row in rows]

            logger.info(f"Created {len(created)} mappings")
            return created

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to bulk create mappings: {e}")
            raise

    async def delete_mappings_for_entity(
        self,
        entity_name: str,
    ) -> int:
        """
        Delete all mappings for entity

        Args:
            entity_name: Entity name

        Returns:
            Number of mappings deleted

        Raises:
            Exception: If deletion fails
        """
        logger.info(f"Deleting all mappings for entity: {entity_name}")

        try:
            stmt = delete(field_mappings_table).where(
                field_mappings_table.c.entity_name == entity_name
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            deleted_count = result.rowcount

            logger.info(f"Deleted {deleted_count} mappings")
            return deleted_count

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete mappings: {e}")
            raise

    async def list_all_entities(self) -> list[str]:
        """
        List all entities that have mappings

        Returns:
            List of unique entity names
        """
        try:
            from sqlalchemy import func

            stmt = select(
                field_mappings_table.c.entity_name
            ).distinct().order_by(field_mappings_table.c.entity_name)

            result = await self.session.execute(stmt)
            rows = result.fetchall()

            return [row.entity_name for row in rows]

        except Exception as e:
            logger.error(f"Failed to list entities: {e}")
            raise

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert SQLAlchemy Row to dict"""
        return {
            "uid": str(row.uid),
            "entity_name": row.entity_name,
            "source_field": row.source_field,
            "target_field": row.target_field,
            "transformation": row.transformation,
            "is_required": row.is_required,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
