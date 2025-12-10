"""
Entity Configuration API Router

Endpoints for managing entity configurations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from math import ceil

from app.db.session import get_session
from app.schemas.entity_schemas import (
    EntityCreateRequest,
    EntityUpdateRequest,
    EntityResponse,
    EntityListResponse,
    EntityListItem,
    EntitySyncStats,
    FieldMappingResponse,
    FieldMappingSchema,
)
from app.repositories.entity_config_repository import EntityConfigRepository
from app.repositories.mapping_repository import MappingRepository
from app.core.config import settings
from datetime import datetime


router = APIRouter(prefix=f"{settings.API_PREFIX}/entities", tags=["Entities"])


@router.get("", response_model=EntityListResponse)
async def list_entities(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    search: str = Query(default=None, description="Search by entity name"),
    sync_enabled: bool = Query(default=None, description="Filter by sync_enabled"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all configured entities with pagination

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)
    - search: Filter by entity name (partial match)
    - sync_enabled: Filter by sync status

    **Returns:**
    - 200: Paginated list of entities with sync stats
    - 500: Server error
    """
    try:
        repo = EntityConfigRepository(session)
        result = await repo.list_entities_with_stats(
            page=page,
            page_size=page_size,
            search=search,
        )

        items = [
            EntityListItem(
                entity_name=item["entity_name"],
                connector_api_slug=item["connector_api_slug"],
                sync_enabled=item["sync_enabled"],
                total_syncs=item["total_syncs"],
                last_sync_at=datetime.fromisoformat(item["last_sync_at"]) if item["last_sync_at"] else None,
                last_sync_status=item["last_sync_status"],
            )
            for item in result["items"]
        ]

        return EntityListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(
    request: EntityCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new entity configuration

    **Request Body:**
    - entity_name: Unique entity name
    - connector_api_slug: APISmith API slug for data fetch
    - business_key_fields: List of fields for business key hash
    - field_mappings: Optional list of field mappings
    - sync_enabled: Enable automatic sync (default: true)
    - sync_schedule: Optional cron expression

    **Returns:**
    - 201: Created entity configuration
    - 400: Validation error
    - 409: Entity already exists
    - 500: Server error
    """
    try:
        entity_repo = EntityConfigRepository(session)
        mapping_repo = MappingRepository(session)

        # Check if entity already exists
        if await entity_repo.entity_exists(request.entity_name):
            raise HTTPException(
                status_code=409,
                detail=f"Entity already exists: {request.entity_name}"
            )

        # Convert parent_refs_config to dict if provided
        parent_refs_dict = None
        if request.parent_refs_config:
            parent_refs_dict = {
                key: {
                    "parent_entity": val.parent_entity,
                    "parent_field": val.parent_field,
                    "child_field": val.child_field,
                }
                for key, val in request.parent_refs_config.items()
            }

        # Create entity config
        entity = await entity_repo.create_entity(
            entity_name=request.entity_name,
            connector_api_slug=request.connector_api_slug,
            business_key_fields=request.business_key_fields,
            sync_enabled=request.sync_enabled,
            sync_schedule=request.sync_schedule,
            parent_refs_config=parent_refs_dict,
        )

        # Create field mappings if provided
        field_mappings = []
        if request.field_mappings:
            mappings_data = [
                {
                    "source_field": m.source_field,
                    "target_field": m.target_field,
                    "transformation": m.transformation,
                    "is_required": m.is_required,
                }
                for m in request.field_mappings
            ]
            created_mappings = await mapping_repo.bulk_create_mappings(
                entity_name=request.entity_name,
                mappings=mappings_data,
            )
            field_mappings = [
                FieldMappingResponse(
                    uid=m["uid"],
                    source_field=m["source_field"],
                    target_field=m["target_field"],
                    transformation=m["transformation"],
                    is_required=m["is_required"],
                    created_at=datetime.fromisoformat(m["created_at"]),
                )
                for m in created_mappings
            ]

        return EntityResponse(
            entity_name=entity["entity_name"],
            connector_api_slug=entity["connector_api_slug"],
            business_key_fields=entity["business_key_fields"],
            sync_enabled=entity["sync_enabled"],
            sync_schedule=entity["sync_schedule"],
            parent_refs_config=entity.get("parent_refs_config"),
            field_mappings=field_mappings,
            sync_stats=None,
            created_at=datetime.fromisoformat(entity["created_at"]),
            updated_at=datetime.fromisoformat(entity["updated_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_name}", response_model=EntityResponse)
async def get_entity(
    entity_name: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get entity configuration by name

    **Path Parameters:**
    - entity_name: Entity name

    **Returns:**
    - 200: Entity configuration with field mappings and sync stats
    - 404: Entity not found
    - 500: Server error
    """
    try:
        entity_repo = EntityConfigRepository(session)
        mapping_repo = MappingRepository(session)

        # Get entity with stats
        entity = await entity_repo.get_entity_with_stats(entity_name)
        if not entity:
            raise HTTPException(
                status_code=404,
                detail=f"Entity not found: {entity_name}"
            )

        # Get field mappings
        mappings = await mapping_repo.get_mappings_for_entity(entity_name)
        field_mappings = [
            FieldMappingResponse(
                uid=m["uid"],
                source_field=m["source_field"],
                target_field=m["target_field"],
                transformation=m["transformation"],
                is_required=m["is_required"],
                created_at=datetime.fromisoformat(m["created_at"]),
            )
            for m in mappings
        ]

        # Build sync stats
        sync_stats = None
        if entity.get("sync_stats"):
            stats = entity["sync_stats"]
            sync_stats = EntitySyncStats(
                total_syncs=stats["total_syncs"],
                successful_syncs=stats["successful_syncs"],
                failed_syncs=stats["failed_syncs"],
                last_sync_at=datetime.fromisoformat(stats["last_sync_at"]) if stats["last_sync_at"] else None,
                last_sync_status=stats["last_sync_status"],
                total_records_synced=stats["total_records_synced"],
            )

        return EntityResponse(
            entity_name=entity["entity_name"],
            connector_api_slug=entity["connector_api_slug"],
            business_key_fields=entity["business_key_fields"],
            sync_enabled=entity["sync_enabled"],
            sync_schedule=entity["sync_schedule"],
            parent_refs_config=entity.get("parent_refs_config"),
            field_mappings=field_mappings,
            sync_stats=sync_stats,
            created_at=datetime.fromisoformat(entity["created_at"]),
            updated_at=datetime.fromisoformat(entity["updated_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{entity_name}", response_model=EntityResponse)
async def update_entity(
    entity_name: str,
    request: EntityUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Update entity configuration

    **Path Parameters:**
    - entity_name: Entity name to update

    **Request Body:**
    - connector_api_slug: New connector API slug
    - business_key_fields: New business key fields
    - sync_enabled: Enable/disable sync
    - sync_schedule: New cron schedule

    **Returns:**
    - 200: Updated entity configuration
    - 404: Entity not found
    - 500: Server error
    """
    try:
        entity_repo = EntityConfigRepository(session)
        mapping_repo = MappingRepository(session)

        # Check if entity exists
        if not await entity_repo.entity_exists(entity_name):
            raise HTTPException(
                status_code=404,
                detail=f"Entity not found: {entity_name}"
            )

        # Convert parent_refs_config if provided
        parent_refs_dict = None
        if request.parent_refs_config:
            parent_refs_dict = {
                key: {
                    "parent_entity": val.parent_entity,
                    "parent_field": val.parent_field,
                    "child_field": val.child_field,
                }
                for key, val in request.parent_refs_config.items()
            }

        # Update entity
        entity = await entity_repo.update_entity(
            entity_name=entity_name,
            connector_api_slug=request.connector_api_slug,
            business_key_fields=request.business_key_fields,
            sync_enabled=request.sync_enabled,
            sync_schedule=request.sync_schedule,
            parent_refs_config=parent_refs_dict,
        )

        # Get field mappings
        mappings = await mapping_repo.get_mappings_for_entity(entity_name)
        field_mappings = [
            FieldMappingResponse(
                uid=m["uid"],
                source_field=m["source_field"],
                target_field=m["target_field"],
                transformation=m["transformation"],
                is_required=m["is_required"],
                created_at=datetime.fromisoformat(m["created_at"]),
            )
            for m in mappings
        ]

        return EntityResponse(
            entity_name=entity["entity_name"],
            connector_api_slug=entity["connector_api_slug"],
            business_key_fields=entity["business_key_fields"],
            sync_enabled=entity["sync_enabled"],
            sync_schedule=entity["sync_schedule"],
            parent_refs_config=entity.get("parent_refs_config"),
            field_mappings=field_mappings,
            sync_stats=None,
            created_at=datetime.fromisoformat(entity["created_at"]),
            updated_at=datetime.fromisoformat(entity["updated_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entity_name}", status_code=204)
async def delete_entity(
    entity_name: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete entity configuration

    Also deletes associated field mappings.

    **Path Parameters:**
    - entity_name: Entity name to delete

    **Returns:**
    - 204: Entity deleted successfully
    - 404: Entity not found
    - 500: Server error
    """
    try:
        entity_repo = EntityConfigRepository(session)

        # Delete entity (cascade deletes mappings)
        deleted = await entity_repo.delete_entity(entity_name)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Entity not found: {entity_name}"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))
