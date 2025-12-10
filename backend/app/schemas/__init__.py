"""
Pydantic Schemas

Request/Response models for API endpoints.
"""

from app.schemas.sync_schemas import (
    SyncStartRequest,
    SyncStartResponse,
    SyncStatusResponse,
    SyncHistoryItem,
    SyncHistoryResponse,
    RetryFailedRequest,
    RetryFailedResponse,
)

from app.schemas.entity_schemas import (
    EntityCreateRequest,
    EntityUpdateRequest,
    EntityResponse,
    EntityListResponse,
    FieldMappingSchema,
)

from app.schemas.monitoring_schemas import (
    StatisticsResponse,
    BatchStatistics,
    FailedRecordResponse,
    PendingChildResponse,
)

from app.schemas.schedule_schemas import (
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleResponse,
    ScheduleListResponse,
    SchedulerStatusResponse,
    ScheduleStatsResponse,
    TriggerSyncRequest,
    TriggerSyncResponse,
)

__all__ = [
    # Sync schemas
    "SyncStartRequest",
    "SyncStartResponse",
    "SyncStatusResponse",
    "SyncHistoryItem",
    "SyncHistoryResponse",
    "RetryFailedRequest",
    "RetryFailedResponse",
    # Entity schemas
    "EntityCreateRequest",
    "EntityUpdateRequest",
    "EntityResponse",
    "EntityListResponse",
    "FieldMappingSchema",
    # Monitoring schemas
    "StatisticsResponse",
    "BatchStatistics",
    "FailedRecordResponse",
    "PendingChildResponse",
    # Schedule schemas
    "ScheduleCreateRequest",
    "ScheduleUpdateRequest",
    "ScheduleResponse",
    "ScheduleListResponse",
    "SchedulerStatusResponse",
    "ScheduleStatsResponse",
    "TriggerSyncRequest",
    "TriggerSyncResponse",
]
