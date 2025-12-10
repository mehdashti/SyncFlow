"""
Field Mapping API Router

Endpoints for managing field mappings.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import List

from app.db.session import get_session
from app.repositories.mapping_repository import MappingRepository
from app.repositories.entity_config_repository import EntityConfigRepository
from app.core.config import settings
from pydantic import BaseModel, Field
from datetime import datetime


router = APIRouter(prefix=f"{settings.API_PREFIX}/mappings", tags=["Field Mappings"])


# ===========================
# Schemas
# ===========================

class MappingCreateRequest(BaseModel):
    """Request to create a field mapping"""
    source_field: str = Field(..., min_length=1, max_length=200)
    target_field: str = Field(..., min_length=1, max_length=200)
    transformation: str | None = Field(default=None, description="uppercase, lowercase, trim, etc.")
    is_required: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "source_field": "ITEM_NO",
                "target_field": "item_number",
                "transformation": "uppercase",
                "is_required": True,
            }
        }


class MappingUpdateRequest(BaseModel):
    """Request to update a field mapping"""
    target_field: str | None = Field(default=None, min_length=1, max_length=200)
    transformation: str | None = Field(default=None)
    is_required: bool | None = Field(default=None)


class MappingResponse(BaseModel):
    """Field mapping response"""
    uid: str
    entity_name: str
    source_field: str
    target_field: str
    transformation: str | None
    is_required: bool
    created_at: datetime


class BulkMappingRequest(BaseModel):
    """Request to bulk create mappings"""
    mappings: List[MappingCreateRequest] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "mappings": [
                    {"source_field": "ITEM_NO", "target_field": "item_number", "is_required": True},
                    {"source_field": "DESCRIPTION", "target_field": "description"},
                    {"source_field": "UOM", "target_field": "unit_of_measure"},
                ]
            }
        }


class BulkMappingResponse(BaseModel):
    """Bulk mapping response"""
    created: int
    mappings: List[MappingResponse]


class MappingListResponse(BaseModel):
    """List of mappings for entity"""
    entity_name: str
    total: int
    mappings: List[MappingResponse]


# ===========================
# Endpoints
# ===========================

@router.get("/{entity_name}", response_model=MappingListResponse)
async def get_entity_mappings(
    entity_name: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get all field mappings for an entity

    **Path Parameters:**
    - entity_name: Entity name

    **Returns:**
    - 200: List of field mappings
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

        # Get mappings
        mappings = await mapping_repo.get_mappings_for_entity(entity_name)

        return MappingListResponse(
            entity_name=entity_name,
            total=len(mappings),
            mappings=[
                MappingResponse(
                    uid=m["uid"],
                    entity_name=m["entity_name"],
                    source_field=m["source_field"],
                    target_field=m["target_field"],
                    transformation=m["transformation"],
                    is_required=m["is_required"],
                    created_at=datetime.fromisoformat(m["created_at"]),
                )
                for m in mappings
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{entity_name}", response_model=MappingResponse, status_code=201)
async def create_mapping(
    entity_name: str,
    request: MappingCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new field mapping for an entity

    **Path Parameters:**
    - entity_name: Entity name

    **Request Body:**
    - source_field: Source field name from APISmith
    - target_field: Target field name in ScheduleHub
    - transformation: Optional transformation (uppercase, lowercase, trim)
    - is_required: Whether field is required

    **Returns:**
    - 201: Created field mapping
    - 404: Entity not found
    - 409: Mapping already exists
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

        # Create mapping
        mapping = await mapping_repo.create_mapping(
            entity_name=entity_name,
            source_field=request.source_field,
            target_field=request.target_field,
            transformation=request.transformation,
            is_required=request.is_required,
        )

        return MappingResponse(
            uid=mapping["uid"],
            entity_name=mapping["entity_name"],
            source_field=mapping["source_field"],
            target_field=mapping["target_field"],
            transformation=mapping["transformation"],
            is_required=mapping["is_required"],
            created_at=datetime.fromisoformat(mapping["created_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Mapping already exists: {request.source_field} -> {request.target_field}"
            )
        logger.error(f"Failed to create mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{entity_name}/{mapping_uid}", response_model=MappingResponse)
async def update_mapping(
    entity_name: str,
    mapping_uid: str,
    request: MappingUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Update a field mapping

    **Path Parameters:**
    - entity_name: Entity name
    - mapping_uid: Mapping UID

    **Request Body:**
    - target_field: New target field name
    - transformation: New transformation
    - is_required: New is_required value

    **Returns:**
    - 200: Updated field mapping
    - 404: Mapping not found
    - 500: Server error
    """
    try:
        mapping_repo = MappingRepository(session)

        # Check if mapping exists
        existing = await mapping_repo.get_mapping(mapping_uid)
        if not existing or existing["entity_name"] != entity_name:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found: {mapping_uid}"
            )

        # Update mapping
        mapping = await mapping_repo.update_mapping(
            mapping_uid=mapping_uid,
            target_field=request.target_field,
            transformation=request.transformation,
            is_required=request.is_required,
        )

        return MappingResponse(
            uid=mapping["uid"],
            entity_name=mapping["entity_name"],
            source_field=mapping["source_field"],
            target_field=mapping["target_field"],
            transformation=mapping["transformation"],
            is_required=mapping["is_required"],
            created_at=datetime.fromisoformat(mapping["created_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entity_name}/{mapping_uid}", status_code=204)
async def delete_mapping(
    entity_name: str,
    mapping_uid: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a field mapping

    **Path Parameters:**
    - entity_name: Entity name
    - mapping_uid: Mapping UID

    **Returns:**
    - 204: Mapping deleted successfully
    - 404: Mapping not found
    - 500: Server error
    """
    try:
        mapping_repo = MappingRepository(session)

        # Check if mapping exists
        existing = await mapping_repo.get_mapping(mapping_uid)
        if not existing or existing["entity_name"] != entity_name:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found: {mapping_uid}"
            )

        # Delete mapping
        await mapping_repo.delete_mapping(mapping_uid)

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{entity_name}/bulk", response_model=BulkMappingResponse, status_code=201)
async def bulk_create_mappings(
    entity_name: str,
    request: BulkMappingRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Bulk create field mappings for an entity

    **Path Parameters:**
    - entity_name: Entity name

    **Request Body:**
    - mappings: List of field mapping definitions

    **Returns:**
    - 201: Created field mappings
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

        # Prepare mappings data
        mappings_data = [
            {
                "source_field": m.source_field,
                "target_field": m.target_field,
                "transformation": m.transformation,
                "is_required": m.is_required,
            }
            for m in request.mappings
        ]

        # Bulk create
        created_mappings = await mapping_repo.bulk_create_mappings(
            entity_name=entity_name,
            mappings=mappings_data,
        )

        return BulkMappingResponse(
            created=len(created_mappings),
            mappings=[
                MappingResponse(
                    uid=m["uid"],
                    entity_name=m["entity_name"],
                    source_field=m["source_field"],
                    target_field=m["target_field"],
                    transformation=m["transformation"],
                    is_required=m["is_required"],
                    created_at=datetime.fromisoformat(m["created_at"]),
                )
                for m in created_mappings
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk create mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entity_name}/all", status_code=204)
async def delete_all_mappings(
    entity_name: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete all field mappings for an entity

    **Path Parameters:**
    - entity_name: Entity name

    **Returns:**
    - 204: All mappings deleted
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

        # Delete all mappings
        await mapping_repo.delete_mappings_for_entity(entity_name)

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
