"""
Monitoring Schemas

Request/Response models for monitoring endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BatchStatistics(BaseModel):
    """Batch statistics by status and entity"""

    total_batches: int
    by_status: Dict[str, int]
    by_entity: Dict[str, int]

    class Config:
        json_schema_extra = {
            "example": {
                "total_batches": 1000,
                "by_status": {
                    "completed": 950,
                    "failed": 30,
                    "running": 10,
                    "pending": 10,
                },
                "by_entity": {
                    "inventory_items": 500,
                    "customers": 300,
                    "sales_orders": 200,
                },
            }
        }


class FailedRecordStatistics(BaseModel):
    """Failed record statistics"""

    total_failed: int
    by_error_type: Dict[str, int]
    by_stage: Dict[str, int]
    by_entity: Dict[str, int]
    retryable: int
    max_retry_exceeded: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_failed": 150,
                "by_error_type": {
                    "validation_error": 100,
                    "insert_error": 50,
                },
                "by_stage": {
                    "normalization": 80,
                    "delta": 40,
                    "ingest": 30,
                },
                "by_entity": {
                    "inventory_items": 100,
                    "customers": 50,
                },
                "retryable": 120,
                "max_retry_exceeded": 30,
            }
        }


class PendingChildStatistics(BaseModel):
    """Pending children statistics"""

    total_pending: int
    by_parent: Dict[str, int]
    by_entity: Dict[str, int]
    max_retry_exceeded: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_pending": 50,
                "by_parent": {
                    "sales_orders": 30,
                    "customers": 20,
                },
                "by_entity": {
                    "sales_order_lines": 30,
                    "contact_persons": 20,
                },
                "max_retry_exceeded": 5,
            }
        }


class StatisticsResponse(BaseModel):
    """Overall system statistics"""

    batches: BatchStatistics
    failed_records: FailedRecordStatistics
    pending_children: PendingChildStatistics
    generated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "batches": {
                    "total_batches": 1000,
                    "by_status": {"completed": 950, "failed": 30},
                    "by_entity": {"inventory_items": 500},
                },
                "failed_records": {
                    "total_failed": 150,
                    "by_error_type": {"validation_error": 100},
                    "by_stage": {"normalization": 80},
                    "by_entity": {"inventory_items": 100},
                    "retryable": 120,
                    "max_retry_exceeded": 30,
                },
                "pending_children": {
                    "total_pending": 50,
                    "by_parent": {"sales_orders": 30},
                    "by_entity": {"sales_order_lines": 30},
                    "max_retry_exceeded": 5,
                },
                "generated_at": "2025-12-08T10:00:00Z",
            }
        }


class FailedRecordResponse(BaseModel):
    """Failed record details"""

    uid: str
    batch_uid: str
    entity_name: str
    record_data: Dict[str, Any]
    error_type: str
    error_message: str
    stage: str
    retry_count: int
    last_retry_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "01234567-89ab-cdef-0123-456789abcdef",
                "batch_uid": "01234567-89ab-cdef-0123-456789abcdef",
                "entity_name": "inventory_items",
                "record_data": {"item_number": "ITEM-001", "description": "Widget"},
                "error_type": "validation_error",
                "error_message": "Missing required field: price",
                "stage": "normalization",
                "retry_count": 2,
                "last_retry_at": "2025-12-08T10:30:00Z",
                "created_at": "2025-12-08T10:00:00Z",
            }
        }


class FailedRecordListResponse(BaseModel):
    """Paginated failed records"""

    items: List[FailedRecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PendingChildResponse(BaseModel):
    """Pending child record details"""

    uid: str
    batch_uid: str
    entity_name: str
    child_bk_hash: str
    child_data: Dict[str, Any]
    parent_entity: str
    parent_bk_hash: str
    retry_count: int
    reason: str
    last_retry_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "01234567-89ab-cdef-0123-456789abcdef",
                "batch_uid": "01234567-89ab-cdef-0123-456789abcdef",
                "entity_name": "sales_order_lines",
                "child_bk_hash": "abc123...",
                "child_data": {"line_number": "001", "quantity": 10},
                "parent_entity": "sales_orders",
                "parent_bk_hash": "def456...",
                "retry_count": 1,
                "reason": "Parent not synced",
                "last_retry_at": None,
                "created_at": "2025-12-08T10:00:00Z",
            }
        }


class PendingChildListResponse(BaseModel):
    """Paginated pending children"""

    items: List[PendingChildResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
