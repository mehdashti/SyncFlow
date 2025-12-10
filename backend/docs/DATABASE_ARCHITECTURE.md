# SyncFlow - Database Architecture

## Design Philosophy

Following APISmith standards:
- **SQLAlchemy Core** (NO ORM)
- Raw SQL with async operations
- Table definitions with metadata
- Type-safe with proper constraints

## Why SQLAlchemy Core (Not ORM)?

1. **Performance**: Direct SQL execution without ORM overhead
2. **Flexibility**: Full control over queries and transactions
3. **Clarity**: Explicit SQL operations, no hidden magic
4. **Consistency**: Same approach as APISmith

## Schema: `bridge`

All tables reside in the `bridge` schema.

### 1. sync_batches

Tracks every sync job execution with detailed metrics.

```sql
Table: bridge.sync_batches
Primary Key: uid (UUID v7)
Indexes:
  - ix_sync_batches_entity (entity_name, started_at)
  - ix_sync_batches_status (status)
```

**Key Fields:**
- `entity_name`: Entity being synced (e.g., "items", "sites")
- `sync_type`: "realtime" or "background"
- `status`: "running", "completed", "failed"
- Metrics: rows_fetched, rows_normalized, rows_inserted, etc.

### 2. failed_records

Dead-letter queue for records that failed processing.

```sql
Table: bridge.failed_records
Primary Key: uid (UUID v7)
Foreign Keys:
  - batch_uid → sync_batches.uid (CASCADE)
Indexes:
  - ix_failed_records_batch (batch_uid)
  - ix_failed_records_retry (next_retry_at) WHERE resolved_at IS NULL
```

**Key Fields:**
- `raw_data`: Original data from APISmith (JSONB)
- `normalized_data`: After normalization (JSONB)
- `stage_failed`: Which stage failed (normalization, mapping, etc.)
- `retry_count`, `max_retries`: Retry logic
- `resolved_at`: When successfully reprocessed

### 3. pending_children

Queue for child records waiting for parent records.

```sql
Table: bridge.pending_children
Primary Key: uid (UUID v7)
Foreign Keys:
  - batch_uid → sync_batches.uid (CASCADE)
Indexes:
  - ix_pending_children_parent (parent_entity, parent_bk_hash)
```

**Key Fields:**
- `child_entity`, `parent_entity`: Relationship definition
- `parent_bk_hash`: Business key hash of missing parent
- `child_payload`: Complete child record (JSONB)
- `retry_count`, `max_retries`: Retry logic

### 4. erp_sync_state

Tracks last sync state per entity for delta detection.

```sql
Table: bridge.erp_sync_state
Primary Key: uid (UUID v7)
Unique: (entity_name, source_system)
Foreign Keys:
  - last_batch_uid → sync_batches.uid (SET NULL)
Indexes:
  - ix_erp_sync_state_entity (entity_name, source_system)
```

**Key Fields:**
- `last_sync_rowversion`: Last processed rowversion (for Oracle delta)
- `last_sync_timestamp`: Last sync time
- `last_batch_uid`: Reference to last successful batch

### 5. background_sync_schedule

Configuration for multi-day background sync of large tables.

```sql
Table: bridge.background_sync_schedule
Primary Key: uid (UUID v7)
Unique: entity_name
```

**Key Fields:**
- `is_enabled`: Enable/disable sync
- `sync_window_start`, `sync_window_end`: Time window (e.g., 19:00-07:00)
- `days_to_complete`: Split sync across N days (default: 7)
- `rows_per_day`: Calculated batch size per day
- `current_offset`: Progress tracking
- `next_run_at`: Next scheduled run

**Example**: Sync 7M rows over 7 days = 1M rows/day during night window

### 6. field_mappings

Field transformation rules from APISmith output to ScheduleHub input.

```sql
Table: bridge.field_mappings
Primary Key: uid (UUID v7)
Unique: (entity_name, source_field, target_field)
Indexes:
  - ix_field_mappings_entity (entity_name)
```

**Key Fields:**
- `source_field`: Field name from APISmith
- `target_field`: Field name for ScheduleHub
- `transformation`: Transformation type (uppercase, trim, etc.)
- `default_value`: Default if source is NULL
- `is_required`: Validation flag

## UUID Strategy

All primary keys use **UUID v7**:
- Time-ordered (better indexing)
- Generated in Python (less DB load)
- Natural sorting by creation time

```python
from uuid_utils import uuid7
uid = uuid7()  # Generate before insert
```

## Timestamps

All timestamps use `TIMESTAMP WITH TIME ZONE` (UTC):
- `created_at`: Auto-generated on insert
- `updated_at`: Auto-updated on modify (where applicable)

## Relationships

```
sync_batches (1) ──┬─> (N) failed_records
                   └─> (N) pending_children
                   └─> (1) erp_sync_state (last_batch_uid)
```

## Indexes Strategy

1. **Query Performance**: Index on frequently queried columns
2. **Foreign Keys**: Always indexed for JOIN performance
3. **Partial Indexes**: For conditional queries (e.g., unresolved records)
4. **Composite Indexes**: For multi-column WHERE clauses

## Data Access Pattern

```python
from sqlalchemy import select, insert, update
from app.db.session import get_session
from app.db.base import sync_batches_table

async with get_session() as session:
    # INSERT
    stmt = insert(sync_batches_table).values(
        uid=uuid7(),
        entity_name="items",
        sync_type="realtime",
        source_system="oracle_ifs",
    )
    await session.execute(stmt)

    # SELECT
    stmt = select(sync_batches_table).where(
        sync_batches_table.c.status == "running"
    )
    result = await session.execute(stmt)
    rows = result.fetchall()

    # UPDATE
    stmt = update(sync_batches_table).where(
        sync_batches_table.c.uid == batch_uid
    ).values(status="completed")
    await session.execute(stmt)
```

## Migration Management

Migrations managed by Alembic:

```bash
# Generate migration (autogenerate from metadata)
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Performance Considerations

1. **JSONB Indexing**: Consider GIN indexes for JSONB fields if querying nested data
2. **Partitioning**: Consider table partitioning for `sync_batches` if >10M rows/year
3. **Archiving**: Archive old batches and failed records periodically
4. **Connection Pooling**: Configured in `session.py` (pool_size=20)

## Security

1. **Schema Isolation**: All tables in dedicated `bridge` schema
2. **User Permissions**: `bridge_user` has full access only to `bridge` schema
3. **No Secrets**: No passwords or tokens stored in tables
4. **Audit Trail**: All tables have `created_at` timestamps

---

See also:
- [app/db/base.py](../app/db/base.py) - Table definitions
- [app/db/session.py](../app/db/session.py) - Session management
- [alembic/](../alembic/) - Migration scripts
