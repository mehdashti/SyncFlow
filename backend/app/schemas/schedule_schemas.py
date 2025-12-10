"""
Schedule API Schemas

Request/Response models for background sync schedule endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, time


class ScheduleCreateRequest(BaseModel):
    """Request to create a background sync schedule"""

    entity_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Entity name (e.g., 'inventory_items')"
    )
    source_system: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Source system identifier"
    )
    sync_window_start: str = Field(
        default="19:00:00",
        description="Start of sync window (HH:MM:SS)"
    )
    sync_window_end: str = Field(
        default="07:00:00",
        description="End of sync window (HH:MM:SS)"
    )
    days_to_complete: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of days to complete full sync"
    )
    rows_per_day: Optional[int] = Field(
        default=None,
        ge=1000,
        description="Target rows per day (auto-calculated if not provided)"
    )
    total_rows_estimate: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated total rows in source"
    )
    is_enabled: bool = Field(
        default=True,
        description="Whether schedule is enabled"
    )

    @field_validator("sync_window_start", "sync_window_end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        try:
            parts = v.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            second = int(parts[2]) if len(parts) > 2 else 0
            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                raise ValueError()
        except:
            raise ValueError("Time must be in HH:MM:SS or HH:MM format")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "inventory_items",
                "source_system": "ifs",
                "sync_window_start": "19:00:00",
                "sync_window_end": "07:00:00",
                "days_to_complete": 7,
                "total_rows_estimate": 7000000,
                "is_enabled": True,
            }
        }


class ScheduleUpdateRequest(BaseModel):
    """Request to update a schedule"""

    sync_window_start: Optional[str] = Field(
        default=None,
        description="Start of sync window (HH:MM:SS)"
    )
    sync_window_end: Optional[str] = Field(
        default=None,
        description="End of sync window (HH:MM:SS)"
    )
    days_to_complete: Optional[int] = Field(
        default=None,
        ge=1,
        le=30,
        description="Number of days to complete full sync"
    )
    rows_per_day: Optional[int] = Field(
        default=None,
        ge=1000,
        description="Target rows per day"
    )
    total_rows_estimate: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated total rows in source"
    )
    is_enabled: Optional[bool] = Field(
        default=None,
        description="Whether schedule is enabled"
    )

    @field_validator("sync_window_start", "sync_window_end")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            parts = v.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            second = int(parts[2]) if len(parts) > 2 else 0
            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                raise ValueError()
        except:
            raise ValueError("Time must be in HH:MM:SS or HH:MM format")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "sync_window_start": "20:00:00",
                "days_to_complete": 5,
                "is_enabled": True,
            }
        }


class ScheduleResponse(BaseModel):
    """Schedule response"""

    uid: str
    entity_name: str
    source_system: str
    is_enabled: bool
    sync_window_start: str
    sync_window_end: str
    days_to_complete: int
    rows_per_day: Optional[int]
    total_rows_estimate: Optional[int]
    current_offset: int
    progress_percent: float
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "01234567-89ab-cdef-0123-456789abcdef",
                "entity_name": "inventory_items",
                "source_system": "ifs",
                "is_enabled": True,
                "sync_window_start": "19:00:00",
                "sync_window_end": "07:00:00",
                "days_to_complete": 7,
                "rows_per_day": 1000000,
                "total_rows_estimate": 7000000,
                "current_offset": 2000000,
                "progress_percent": 28.57,
                "last_run_at": "2025-12-08T03:00:00Z",
                "next_run_at": "2025-12-09T19:00:00Z",
                "created_at": "2025-12-01T10:00:00Z",
                "updated_at": "2025-12-08T03:00:00Z",
            }
        }


class ScheduleListResponse(BaseModel):
    """List of schedules response"""

    items: List[ScheduleResponse]
    total: int
    page: int
    page_size: int
    pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 10,
                "page": 1,
                "page_size": 50,
                "pages": 1,
            }
        }


class SchedulerStatusResponse(BaseModel):
    """Scheduler service status"""

    is_running: bool
    enabled_schedules: int
    active_jobs: int
    jobs: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "is_running": True,
                "enabled_schedules": 5,
                "active_jobs": 5,
                "jobs": [
                    {
                        "job_id": "sync_inventory_items",
                        "entity_name": "inventory_items",
                        "next_run": "2025-12-09T19:00:00Z",
                        "pending": False,
                    }
                ],
            }
        }


class ScheduleStatsResponse(BaseModel):
    """Schedule statistics"""

    total_schedules: int
    enabled_schedules: int
    disabled_schedules: int
    average_progress_percent: float

    class Config:
        json_schema_extra = {
            "example": {
                "total_schedules": 10,
                "enabled_schedules": 8,
                "disabled_schedules": 2,
                "average_progress_percent": 45.5,
            }
        }


class TriggerSyncRequest(BaseModel):
    """Request to manually trigger a scheduled sync"""

    force: bool = Field(
        default=False,
        description="Force run even outside time window"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "force": False,
            }
        }


class TriggerSyncResponse(BaseModel):
    """Response after triggering sync"""

    success: bool
    message: str
    job_id: Optional[str]
    scheduled_for: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Sync triggered successfully",
                "job_id": "sync_inventory_items_manual_1234567890",
                "scheduled_for": "2025-12-08T14:30:00Z",
            }
        }
