"""
Entity Configuration Schemas

Request/Response models for entity management endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ParentRefConfig(BaseModel):
    """Parent reference configuration for FK resolution"""

    parent_entity: str = Field(..., description="Parent entity name (e.g., 'sites')")
    parent_field: str = Field(..., description="Field in parent's business key (e.g., 'site_id')")
    child_field: str = Field(..., description="Field in child record containing parent reference (e.g., 'site_id')")

    class Config:
        json_schema_extra = {
            "example": {
                "parent_entity": "sites",
                "parent_field": "site_id",
                "child_field": "site_id",
            }
        }


class FieldMappingSchema(BaseModel):
    """Field mapping configuration"""

    source_field: str = Field(..., min_length=1, max_length=100, description="Source field name from APISmith")
    target_field: str = Field(..., min_length=1, max_length=100, description="Target field name in ScheduleHub")
    transformation: Optional[str] = Field(default=None, description="Transformation: uppercase, lowercase, trim, etc.")
    is_required: bool = Field(default=False, description="Whether field is required")

    class Config:
        json_schema_extra = {
            "example": {
                "source_field": "ITEM_NO",
                "target_field": "item_number",
                "transformation": "uppercase",
                "is_required": True,
            }
        }


class EntityCreateRequest(BaseModel):
    """Request to create entity configuration"""

    entity_name: str = Field(..., min_length=1, max_length=100, description="Entity name")
    connector_api_slug: str = Field(..., min_length=1, max_length=100, description="APISmith API slug")
    business_key_fields: List[str] = Field(..., min_items=1, description="Business key fields")
    field_mappings: List[FieldMappingSchema] = Field(default_factory=list, description="Field mappings")
    sync_enabled: bool = Field(default=True, description="Enable automatic sync")
    sync_schedule: Optional[str] = Field(default=None, description="Cron expression for scheduled sync")
    parent_refs_config: Optional[Dict[str, ParentRefConfig]] = Field(
        default=None,
        description="Parent references configuration for FK resolution"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "work_centers",
                "connector_api_slug": "work_centers",
                "business_key_fields": ["work_center_id"],
                "field_mappings": [
                    {
                        "source_field": "WORK_CENTER_ID",
                        "target_field": "work_center_id",
                        "transformation": "uppercase",
                        "is_required": True,
                    },
                    {
                        "source_field": "DESCRIPTION",
                        "target_field": "description",
                        "transformation": None,
                        "is_required": False,
                    },
                ],
                "sync_enabled": True,
                "sync_schedule": "0 */6 * * *",
                "parent_refs_config": {
                    "site": {
                        "parent_entity": "sites",
                        "parent_field": "site_id",
                        "child_field": "site_id",
                    },
                    "work_area": {
                        "parent_entity": "work_areas",
                        "parent_field": "work_area_id",
                        "child_field": "work_area_id",
                    },
                },
            }
        }


class EntityUpdateRequest(BaseModel):
    """Request to update entity configuration"""

    connector_api_slug: Optional[str] = Field(default=None, description="APISmith API slug")
    business_key_fields: Optional[List[str]] = Field(default=None, description="Business key fields")
    sync_enabled: Optional[bool] = Field(default=None, description="Enable automatic sync")
    sync_schedule: Optional[str] = Field(default=None, description="Cron expression for scheduled sync")
    parent_refs_config: Optional[Dict[str, ParentRefConfig]] = Field(
        default=None,
        description="Parent references configuration for FK resolution"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sync_enabled": False,
                "sync_schedule": None,
                "parent_refs_config": {
                    "site": {
                        "parent_entity": "sites",
                        "parent_field": "site_id",
                        "child_field": "site_id",
                    },
                },
            }
        }


class FieldMappingResponse(BaseModel):
    """Field mapping response"""

    uid: str
    source_field: str
    target_field: str
    transformation: Optional[str] = None
    is_required: bool
    created_at: datetime


class EntitySyncStats(BaseModel):
    """Entity sync statistics"""

    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    total_records_synced: int


class EntityResponse(BaseModel):
    """Entity configuration response"""

    entity_name: str
    connector_api_slug: str
    business_key_fields: List[str]
    sync_enabled: bool
    sync_schedule: Optional[str] = None
    parent_refs_config: Optional[Dict[str, Any]] = None
    field_mappings: List[FieldMappingResponse]
    sync_stats: Optional[EntitySyncStats] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "work_centers",
                "connector_api_slug": "work_centers",
                "business_key_fields": ["work_center_id"],
                "sync_enabled": True,
                "sync_schedule": "0 */6 * * *",
                "parent_refs_config": {
                    "site": {
                        "parent_entity": "sites",
                        "parent_field": "site_id",
                        "child_field": "site_id",
                    },
                },
                "field_mappings": [
                    {
                        "uid": "01234567-89ab-cdef-0123-456789abcdef",
                        "source_field": "WORK_CENTER_ID",
                        "target_field": "work_center_id",
                        "transformation": "uppercase",
                        "is_required": True,
                        "created_at": "2025-12-08T10:00:00Z",
                    }
                ],
                "sync_stats": {
                    "total_syncs": 100,
                    "successful_syncs": 98,
                    "failed_syncs": 2,
                    "last_sync_at": "2025-12-08T10:00:00Z",
                    "last_sync_status": "completed",
                    "total_records_synced": 50000,
                },
                "created_at": "2025-12-01T10:00:00Z",
                "updated_at": "2025-12-08T10:00:00Z",
            }
        }


class EntityListItem(BaseModel):
    """Single entity in list"""

    entity_name: str
    connector_api_slug: str
    sync_enabled: bool
    total_syncs: int
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None


class EntityListResponse(BaseModel):
    """Paginated entity list"""

    items: List[EntityListItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "entity_name": "inventory_items",
                        "connector_api_slug": "inventory_items",
                        "sync_enabled": True,
                        "total_syncs": 100,
                        "last_sync_at": "2025-12-08T10:00:00Z",
                        "last_sync_status": "completed",
                    }
                ],
                "total": 10,
                "page": 1,
                "page_size": 50,
                "total_pages": 1,
            }
        }
