"""
Sync API Schemas

Request/Response models for sync endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class SyncStartRequest(BaseModel):
    """Request to start sync for entity"""

    entity_name: str = Field(..., min_length=1, max_length=100, description="Entity name (e.g., 'inventory_items')")
    connector_api_slug: str = Field(..., min_length=1, max_length=100, description="APISmith API slug")
    business_key_fields: List[str] = Field(..., min_items=1, description="Fields forming business key")
    sync_type: str = Field(default="incremental", description="Sync type: 'full' or 'incremental'")
    page_size: int = Field(default=1000, ge=100, le=10000, description="Records per page")
    max_pages: Optional[int] = Field(default=None, ge=1, description="Max pages to fetch (for testing)")

    @field_validator("sync_type")
    @classmethod
    def validate_sync_type(cls, v: str) -> str:
        if v not in ["full", "incremental", "background"]:
            raise ValueError("sync_type must be 'full', 'incremental', or 'background'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "inventory_items",
                "connector_api_slug": "inventory_items",
                "business_key_fields": ["item_number"],
                "sync_type": "incremental",
                "page_size": 1000,
            }
        }


class SyncStartResponse(BaseModel):
    """Response after starting sync"""

    success: bool
    batch_uid: str
    entity_name: str
    sync_type: str
    message: str
    started_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "batch_uid": "01234567-89ab-cdef-0123-456789abcdef",
                "entity_name": "inventory_items",
                "sync_type": "incremental",
                "message": "Sync started successfully",
                "started_at": "2025-12-08T10:30:00Z",
            }
        }


class SyncMetrics(BaseModel):
    """Sync metrics"""

    total_fetched: int
    total_processed: int
    inserted: int
    updated: int
    deleted: int
    skipped: int
    failed: int
    efficiency_percent: float

    class Config:
        json_schema_extra = {
            "example": {
                "total_fetched": 1000,
                "total_processed": 1000,
                "inserted": 100,
                "updated": 50,
                "deleted": 5,
                "skipped": 845,
                "failed": 0,
                "efficiency_percent": 84.5,
            }
        }


class SyncStatusResponse(BaseModel):
    """Sync batch status"""

    batch_uid: str
    entity_name: str
    sync_type: str
    status: str  # pending, running, completed, failed
    connector_api_slug: Optional[str] = None
    total_records: int
    records_processed: int
    records_inserted: int
    records_updated: int
    records_deleted: int
    records_skipped: int
    records_failed: int
    last_rowversion: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "batch_uid": "01234567-89ab-cdef-0123-456789abcdef",
                "entity_name": "inventory_items",
                "sync_type": "incremental",
                "status": "completed",
                "connector_api_slug": "inventory_items",
                "total_records": 1000,
                "records_processed": 1000,
                "records_inserted": 100,
                "records_updated": 50,
                "records_deleted": 5,
                "records_skipped": 845,
                "records_failed": 0,
                "last_rowversion": "2025-12-08 10:30:00",
                "error_message": None,
                "started_at": "2025-12-08T10:00:00Z",
                "completed_at": "2025-12-08T10:05:00Z",
                "created_at": "2025-12-08T10:00:00Z",
            }
        }


class SyncHistoryItem(BaseModel):
    """Single sync history item"""

    batch_uid: str
    entity_name: str
    sync_type: str
    status: str
    total_records: int
    records_processed: int
    records_inserted: int
    records_updated: int
    records_deleted: int
    records_skipped: int
    records_failed: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class SyncHistoryResponse(BaseModel):
    """Paginated sync history"""

    items: List[SyncHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "batch_uid": "01234567-89ab-cdef-0123-456789abcdef",
                        "entity_name": "inventory_items",
                        "sync_type": "incremental",
                        "status": "completed",
                        "total_records": 1000,
                        "records_processed": 1000,
                        "records_inserted": 100,
                        "records_updated": 50,
                        "records_deleted": 5,
                        "records_skipped": 845,
                        "records_failed": 0,
                        "started_at": "2025-12-08T10:00:00Z",
                        "completed_at": "2025-12-08T10:05:00Z",
                        "created_at": "2025-12-08T10:00:00Z",
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 50,
                "total_pages": 2,
            }
        }


class RetryFailedRequest(BaseModel):
    """Request to retry failed records"""

    batch_uid: Optional[str] = Field(default=None, description="Specific batch UID to retry")
    entity_name: Optional[str] = Field(default=None, description="Entity name to retry")
    max_retries: int = Field(default=3, ge=1, le=10, description="Max retry attempts")
    limit: int = Field(default=100, ge=1, le=1000, description="Max records to retry")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_uid": "01234567-89ab-cdef-0123-456789abcdef",
                "entity_name": None,
                "max_retries": 3,
                "limit": 100,
            }
        }


class RetryFailedResponse(BaseModel):
    """Response after retrying failed records"""

    success: bool
    message: str
    records_retried: int
    records_resolved: int
    records_still_failed: int

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Retry completed",
                "records_retried": 10,
                "records_resolved": 8,
                "records_still_failed": 2,
            }
        }
