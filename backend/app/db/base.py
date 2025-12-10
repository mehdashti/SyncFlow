"""
Database Base Module - SQLAlchemy Core (NO ORM)

Following APISmith architecture:
- Uses SQLAlchemy Core with Table definitions
- NO ORM models
- Raw SQL with async operations
"""

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Integer,
    Boolean,
    Text,
    Numeric,
    Time,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

from app.core.config import settings


# Metadata object for schema (SQLAlchemy Core)
metadata = MetaData(schema=settings.POSTGRES_SCHEMA)


# ===========================
# Helper Functions
# ===========================

def pk_uid(column_name: str = "uid") -> Column:
    """
    Primary key UUID v7 with Python-side generation.

    UUID v7 must be generated in Python before insert using:
        from uuid_utils import uuid7
        uid = uuid7()
    """
    return Column(
        column_name,
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )


def audit_columns():
    """Standard audit columns (UTC timestamps)"""
    return [
        Column(
            "created_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    ]


def audit_columns_with_update():
    """Audit columns with update timestamp"""
    return [
        Column(
            "created_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        Column(
            "updated_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    ]


# ===========================
# Table Definitions (SQLAlchemy Core)
# ===========================

# 1. sync_batches - Batch tracking
sync_batches_table = Table(
    "sync_batches",
    metadata,
    pk_uid(),
    Column("entity_name", String(100), nullable=False),
    Column("sync_type", String(50), nullable=False),  # 'realtime' | 'background'
    Column("source_system", String(100), nullable=False),
    Column("started_at", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    Column("completed_at", TIMESTAMP(timezone=True), nullable=True),
    Column("status", String(50), nullable=False, server_default="running"),
    # Metrics
    Column("rows_fetched", Integer, nullable=False, server_default="0"),
    Column("rows_normalized", Integer, nullable=False, server_default="0"),
    Column("rows_validated", Integer, nullable=False, server_default="0"),
    Column("rows_mapped", Integer, nullable=False, server_default="0"),
    Column("rows_inserted", Integer, nullable=False, server_default="0"),
    Column("rows_updated", Integer, nullable=False, server_default="0"),
    Column("rows_deleted", Integer, nullable=False, server_default="0"),
    Column("rows_failed", Integer, nullable=False, server_default="0"),
    Column("success_rate", Numeric(5, 2), nullable=True),
    Column("error_message", Text, nullable=True),
    *audit_columns(),
)

Index("ix_sync_batches_entity", sync_batches_table.c.entity_name, sync_batches_table.c.started_at)
Index("ix_sync_batches_status", sync_batches_table.c.status)


# 2. failed_records - Dead-letter queue
failed_records_table = Table(
    "failed_records",
    metadata,
    pk_uid(),
    Column(
        "batch_uid",
        UUID(as_uuid=True),
        ForeignKey(f"{settings.POSTGRES_SCHEMA}.sync_batches.uid", ondelete="CASCADE"),
        nullable=True,
    ),
    Column("entity_name", String(100), nullable=False),
    Column("source_system", String(100), nullable=False),
    # Data snapshots
    Column("raw_data", JSONB, nullable=False),
    Column("normalized_data", JSONB, nullable=True),
    Column("mapped_data", JSONB, nullable=True),
    # Error details
    Column("stage_failed", String(50), nullable=False),
    Column("error_type", String(100), nullable=False),
    Column("error_message", Text, nullable=False),
    Column("stack_trace", Text, nullable=True),
    # Retry logic
    Column("retry_count", Integer, nullable=False, server_default="0"),
    Column("max_retries", Integer, nullable=False, server_default="3"),
    Column("next_retry_at", TIMESTAMP(timezone=True), nullable=True),
    # Resolution
    Column("resolved_at", TIMESTAMP(timezone=True), nullable=True),
    Column("resolved_by", String(100), nullable=True),
    *audit_columns(),
)

Index("ix_failed_records_batch", failed_records_table.c.batch_uid)
Index(
    "ix_failed_records_retry",
    failed_records_table.c.next_retry_at,
    postgresql_where=failed_records_table.c.resolved_at.is_(None),
)


# 3. pending_children - Parent-child resolution queue
pending_children_table = Table(
    "pending_children",
    metadata,
    pk_uid(),
    Column(
        "batch_uid",
        UUID(as_uuid=True),
        ForeignKey(f"{settings.POSTGRES_SCHEMA}.sync_batches.uid", ondelete="CASCADE"),
        nullable=True,
    ),
    Column("child_entity", String(100), nullable=False),
    Column("parent_entity", String(100), nullable=False),
    Column("parent_bk_hash", String(128), nullable=False),
    Column("child_payload", JSONB, nullable=False),
    # Retry logic
    Column("retry_count", Integer, nullable=False, server_default="0"),
    Column("max_retries", Integer, nullable=False, server_default="5"),
    Column("next_retry_at", TIMESTAMP(timezone=True), nullable=True),
    # Resolution
    Column("resolved_at", TIMESTAMP(timezone=True), nullable=True),
    *audit_columns(),
)

Index("ix_pending_children_parent", pending_children_table.c.parent_entity, pending_children_table.c.parent_bk_hash)


# 4. erp_sync_state - Delta detection state
erp_sync_state_table = Table(
    "erp_sync_state",
    metadata,
    pk_uid(),
    Column("entity_name", String(100), nullable=False),
    Column("source_system", String(100), nullable=False),
    # Delta detection state
    Column("last_sync_rowversion", String(255), nullable=True),
    Column("last_sync_timestamp", TIMESTAMP(timezone=True), nullable=True),
    Column(
        "last_batch_uid",
        UUID(as_uuid=True),
        ForeignKey(f"{settings.POSTGRES_SCHEMA}.sync_batches.uid", ondelete="SET NULL"),
        nullable=True,
    ),
    *audit_columns_with_update(),
    UniqueConstraint("entity_name", "source_system", name="uq_erp_sync_state_entity_system"),
)

Index("ix_erp_sync_state_entity", erp_sync_state_table.c.entity_name, erp_sync_state_table.c.source_system)


# 5. background_sync_schedule - Background sync configuration
background_sync_schedule_table = Table(
    "background_sync_schedule",
    metadata,
    pk_uid(),
    Column("entity_name", String(100), nullable=False, unique=True),
    Column("source_system", String(100), nullable=False),
    Column("is_enabled", Boolean, nullable=False, server_default="true"),
    # Time window
    Column("sync_window_start", Time, nullable=False, server_default="19:00:00"),
    Column("sync_window_end", Time, nullable=False, server_default="07:00:00"),
    # Multi-day sync configuration
    Column("days_to_complete", Integer, nullable=False, server_default="7"),
    Column("rows_per_day", Integer, nullable=True),
    Column("total_rows_estimate", Integer, nullable=True),
    # Current progress
    Column("current_offset", Integer, nullable=False, server_default="0"),
    # Schedule tracking
    Column("last_run_at", TIMESTAMP(timezone=True), nullable=True),
    Column("next_run_at", TIMESTAMP(timezone=True), nullable=True),
    *audit_columns_with_update(),
)


# 6. entity_config - Entity configuration
entity_config_table = Table(
    "entity_config",
    metadata,
    pk_uid(),
    Column("entity_name", String(100), nullable=False, unique=True),
    Column("connector_api_slug", String(100), nullable=False),
    Column("business_key_fields", JSONB, nullable=False),  # List of field names
    Column("sync_enabled", Boolean, nullable=False, server_default="true"),
    Column("sync_schedule", String(100), nullable=True),  # Cron expression
    # Parent references configuration for FK resolution
    # Format: {"site": {"parent_entity": "sites", "parent_field": "site_id", "child_field": "site_id"}, ...}
    Column("parent_refs_config", JSONB, nullable=True),
    *audit_columns_with_update(),
)

Index("ix_entity_config_name", entity_config_table.c.entity_name)


# 7. field_mappings - Field transformation rules
field_mappings_table = Table(
    "field_mappings",
    metadata,
    pk_uid(),
    Column("entity_name", String(100), nullable=False),
    Column("source_field", String(200), nullable=False),
    Column("target_field", String(200), nullable=False),
    # Transformation rules
    Column("transformation", String(50), nullable=True),
    Column("default_value", Text, nullable=True),
    # Validation
    Column("is_required", Boolean, nullable=False, server_default="false"),
    Column("validation_rule", Text, nullable=True),
    *audit_columns(),
    UniqueConstraint("entity_name", "source_field", "target_field", name="uq_field_mapping_entity_source_target"),
)

Index("ix_field_mappings_entity", field_mappings_table.c.entity_name)


# Export all tables
__all__ = [
    "metadata",
    "sync_batches_table",
    "failed_records_table",
    "pending_children_table",
    "erp_sync_state_table",
    "background_sync_schedule_table",
    "entity_config_table",
    "field_mappings_table",
]
