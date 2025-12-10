# SyncFlow - Architecture Overview

## System Context

SyncFlow is the **data integration middleware** between APISmith and ScheduleHub.

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│ APISmith│─────>│  SyncFlow   │─────>│ ScheduleHub │
│   (ERP)     │ JSON │ (Transform)  │ JSON │   (Target)   │
└─────────────┘      └──────────────┘      └──────────────┘
     Oracle              9-Stage              PostgreSQL
     IFS/EBS            Pipeline             UUID-based
```

## Core Responsibilities

1. **Data Normalization**: Clean and standardize ERP data (5 layers)
2. **Identity Generation**: Create business key and data hashes
3. **Delta Detection**: Identify INSERT/UPDATE/DELETE operations
4. **Parent-Child Resolution**: Handle foreign key dependencies
5. **Batch Orchestration**: Manage sync jobs with metrics
6. **Error Handling**: Dead-letter queue with retry logic
7. **Background Sync**: Multi-day sync for large tables (7M rows)

---

## 9-Stage Pipeline

### Stage 1: FETCH
**Component**: `services/connector_client/`

- Fetch data from APISmith API
- Handle pagination (1000 rows/page)
- Support query parameters (filters, rowversion)
- JWT authentication

**Input**: API request
**Output**: Raw JSON rows from Oracle

---

### Stage 2: NORMALIZE (5 Layers)
**Component**: `services/normalization/`

**Layer 1: Type Coercion**
- Oracle types → Python types
- VARCHAR2, NUMBER, DATE, TIMESTAMP, RAW
- NULL handling

**Layer 2: String Normalization**
- Trim whitespace
- Remove control characters
- Normalize line endings

**Layer 3: Numeric Normalization**
- Parse "10,000" → 10000
- Handle currency symbols
- Scientific notation

**Layer 4: DateTime Normalization**
- Multiple date formats → ISO 8601
- Timezone conversion

**Layer 5: Field Mapping**
- Source → Target field names
- Apply transformations (uppercase, trim, etc.)
- Default values
- Required field validation

**Input**: Raw rows
**Output**: Normalized rows

---

### Stage 3: VALIDATE
**Component**: `services/normalization/layer_5_field_mapping.py`

- Check required fields
- Validate data types
- Business rule validation (future)

**Input**: Normalized rows
**Output**: Valid rows (invalid → failed_records)

---

### Stage 4: MAP
**Component**: `services/normalization/layer_5_field_mapping.py`

- Apply field transformations
- Rename fields for ScheduleHub
- Add computed fields (future)

**Input**: Valid rows
**Output**: Mapped rows

---

### Stage 5: IDENTITY
**Component**: `services/identity/`

Generate two critical hashes:

**BK_HASH (Business Key Hash)**
- Identifies unique records
- Based on business key fields (e.g., item_number)
- xxHash128 hash of canonical string (32-char hex)
- Example: `xxHash128("item_number=PART-12345")`
- Used for: Record matching, upsert logic

**DATA_HASH**
- Detects data changes
- Based on ALL data fields (sorted alphabetically)
- BLAKE3 hash of canonical string (64-char hex)
- Example: `BLAKE3("desc=Widget|price=10.50|uom=EA")`
- Used for: Delta detection, skip unchanged records

**ROWVERSION**
- Oracle rowversion/timestamp
- Used for: Fast delta queries

**Input**: Mapped rows
**Output**: Rows with `erp_key_hash`, `erp_data_hash`, `erp_rowversion`

---

### Stage 6: DELTA
**Component**: `services/delta/`

Determine operation type for each record:

**Strategy 1: Rowversion-based** (Fast)
- Query ScheduleHub: records with rowversion > last_sync
- Compare incoming rowversion vs stored
- Decision: INSERT (new) | UPDATE (changed) | SKIP (unchanged)

**Strategy 2: Hash-based** (Fallback)
- Query ScheduleHub: all records by BK_HASH
- Compare DATA_HASH
- Decision: INSERT (new) | UPDATE (changed) | SKIP (unchanged)

**DELETE Detection**
- Compare BK_HASH in APISmith vs ScheduleHub
- Missing in APISmith → DELETE

**Input**: Rows with identity
**Output**: Categorized rows (insert_list, update_list, delete_list, skip_list)

---

### Stage 7: RESOLVE
**Component**: `services/parent_child/`

Handle parent-child dependencies:

**Problem**: Child arrives before parent
```
Order Line (child) → Order (parent not yet synced)
```

**Solution**:
1. Check if parent exists in ScheduleHub (by parent BK_HASH)
2. If NOT found → Queue in `pending_children` table
3. If found → Continue to Stage 8
4. Background job retries pending children periodically
5. Max 5 retries with exponential backoff

**Input**: Delta-categorized rows
**Output**: Rows ready for ingestion (others queued)

---

### Stage 8: INGEST
**Component**: `services/smartplan_client/`

Send data to ScheduleHub:

**INSERT**
- `POST /api/v1/{entity}`
- ScheduleHub generates UUID

**UPDATE**
- `PATCH /api/v1/{entity}/{uid}`
- Lookup UUID by BK_HASH first

**DELETE**
- `DELETE /api/v1/{entity}/{uid}`

**Batch Operations** (Future)
- `POST /api/v1/{entity}/batch`
- Up to 1000 records per request

**Input**: Resolved rows with operations
**Output**: Success/failure per row

---

### Stage 9: TRACK
**Component**: `repositories/batch_repository.py`

Update batch metrics in `sync_batches` table:

**Metrics Tracked**:
- `rows_fetched`: From APISmith
- `rows_normalized`: After normalization
- `rows_validated`: Valid records
- `rows_mapped`: After field mapping
- `rows_inserted`: Successfully inserted
- `rows_updated`: Successfully updated
- `rows_deleted`: Successfully deleted
- `rows_failed`: Errors
- `success_rate`: % successful
- `error_message`: First error encountered

**Failed Records**:
- Store in `failed_records` table
- Include: raw_data, normalized_data, mapped_data
- Track: stage_failed, error_type, error_message
- Retry logic: max 3 retries with exponential backoff

**Input**: Ingestion results
**Output**: Updated batch record

---

## Technology Stack

### Backend
- **Language**: Python 3.13
- **Framework**: FastAPI 0.115+
- **ASGI Server**: Uvicorn with uvloop
- **Package Manager**: uv (fast Rust-based)

### Database
- **Engine**: PostgreSQL 18
- **ORM**: SQLAlchemy Core (NOT ORM)
- **Migrations**: Alembic (async)
- **Connection Pooling**: asyncpg (pool_size=20)
- **Schema**: `bridge` (dedicated)

### Data Processing
- **Hashing**: xxHash128 for BK_HASH (32-char hex), BLAKE3 for DATA_HASH (64-char hex)
- **UUID**: UUID v7 (time-ordered)
- **Date Parsing**: python-dateutil
- **Logging**: Loguru (structured, rotated)

### HTTP Clients
- **Library**: httpx (async)
- **Auth**: JWT tokens (service-to-service)
- **Retry**: Exponential backoff
- **Timeout**: 30s per request

### Scheduling
- **Library**: APScheduler
- **Jobs**: Background sync, retry failed records, resolve pending children
- **Execution**: Async

### Monitoring
- **Metrics**: Prometheus client
- **Health Checks**: `/api/v1/health`
- **Logs**: Structured JSON logs with correlation IDs

---

## Data Flow Example

### Scenario: Sync 1000 Items from Oracle IFS

```
1. API Request: POST /api/v1/sync/start {"entity": "items"}

2. FETCH Stage:
   - Query APISmith: GET /api/v1/runtime/items/execute?limit=1000
   - Receive 1000 rows (raw Oracle data)

3. NORMALIZE Stage (5 layers):
   Layer 1: part_no (VARCHAR2) → "PART-12345" (str)
   Layer 2: "  PART-12345  " → "PART-12345" (trimmed)
   Layer 3: list_price "1,000.50" → 1000.50 (float)
   Layer 4: creation_date "2025-12-08" → "2025-12-08T00:00:00" (ISO)
   Layer 5: part_no → item_number, apply uppercase → "PART-12345"

4. VALIDATE Stage:
   - Check required fields (item_number, description)
   - 998 valid, 2 missing item_number → failed_records

5. MAP Stage:
   - Rename fields for ScheduleHub schema
   - Add default values where configured

6. IDENTITY Stage:
   - BK_HASH: xxHash128("item_number=PART-12345") → 32-char hex
   - DATA_HASH: BLAKE3("description=Widget|item_number=PART-12345|list_price=1000.5|uom=EA") → 64-char hex
   - ROWVERSION: "2025-12-08 10:30:00.123456"

7. DELTA Stage:
   - Query ScheduleHub: GET /api/v1/items?erp_key_hash=abc123...
   - Compare DATA_HASH:
     - 50 new items → INSERT
     - 900 unchanged → SKIP
     - 48 changed → UPDATE

8. RESOLVE Stage:
   - No parent dependencies for items
   - All 98 records ready for ingestion

9. INGEST Stage:
   - POST /api/v1/items (50 inserts) → 50 success
   - PATCH /api/v1/items/{uid} (48 updates) → 47 success, 1 conflict

10. TRACK Stage:
    - Update sync_batches:
      - rows_fetched: 1000
      - rows_normalized: 998
      - rows_validated: 998
      - rows_inserted: 50
      - rows_updated: 47
      - rows_failed: 3 (2 validation + 1 conflict)
      - success_rate: 99.70%
    - Store 3 failed records in failed_records table
```

**Result**: 97/98 records ingested successfully (1 conflict to retry)

---

## Database Schema

See [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) for complete details.

**6 Core Tables**:
1. `sync_batches` - Batch tracking
2. `failed_records` - Dead-letter queue
3. `pending_children` - Parent-child queue
4. `erp_sync_state` - Delta state
5. `background_sync_schedule` - Multi-day sync config
6. `field_mappings` - Transformation rules

---

## Configuration

### Environment Variables

See [.env.example](../.env.example) for complete list.

**Key Settings**:
```bash
# APISmith
APISmith_URL=http://127.0.0.1:8007
APISmith_TOKEN=<service-jwt>

# ScheduleHub
ScheduleHub_URL=http://127.0.0.1:5180
ScheduleHub_TOKEN=<service-jwt>

# Sync Configuration
DEFAULT_BATCH_SIZE=1000
MAX_BATCH_SIZE=10000
SYNC_WORKER_THREADS=4

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY_SECONDS=60
```

---

## Scalability

### Horizontal Scaling
- **Stateless**: SyncFlow instances share PostgreSQL state
- **Load Balancer**: Distribute sync jobs across instances
- **Job Queue**: Use RabbitMQ/Redis for job distribution (future)

### Performance Optimizations
1. **Batch Processing**: 1000 rows per batch (configurable)
2. **Connection Pooling**: 20 connections to PostgreSQL
3. **Async I/O**: Non-blocking HTTP and database operations
4. **Skip Unchanged**: Delta detection avoids unnecessary updates
5. **Parallel Syncs**: Multiple entities sync concurrently

### Capacity
- **Target**: 1M rows in <10 seconds
- **Background Sync**: 7M rows over 7 days (1M/day)
- **Concurrent Jobs**: 4 workers (configurable)

---

## Error Handling

### Error Types

**1. APISmith Errors**
- Connection timeout → Retry with backoff
- 5xx errors → Retry
- 4xx errors → Log and skip

**2. Normalization Errors**
- Invalid data type → Store in failed_records
- Missing required field → Store in failed_records
- Log error with stack trace

**3. ScheduleHub Errors**
- 409 Conflict → Check if record exists, retry as UPDATE
- 404 Parent Missing → Queue in pending_children
- 5xx → Retry

**4. Database Errors**
- Connection lost → Reconnect with pool
- Deadlock → Retry transaction
- Constraint violation → Log and skip

### Retry Strategy

**Failed Records**:
- Max 3 retries
- Exponential backoff: 60s, 120s, 240s
- Manual resolution after max retries

**Pending Children**:
- Max 5 retries
- Check every 5 minutes
- Resolve when parent found

---

## Security

### Authentication
- **Service-to-Service**: JWT tokens
- **Token Generation**: Shared secret (INTERNAL_SERVICE_JWT_SECRET)
- **Token Validation**: HS256 algorithm

### Data Protection
- **Encryption**: TLS for all HTTP requests
- **Secrets**: Environment variables (not in code)
- **Database**: SSL connections to PostgreSQL

### Access Control
- **Database User**: Limited to `bridge` schema only
- **No Root Access**: SyncFlow user cannot access other schemas

---

## Monitoring & Observability

### Metrics (Prometheus)
- `bridge_sync_total` - Total sync jobs
- `bridge_sync_duration_seconds` - Job duration
- `bridge_rows_processed` - Rows per entity
- `bridge_errors_total` - Error count by type

### Logs (Structured JSON)
```json
{
  "timestamp": "2025-12-08T14:30:00Z",
  "level": "INFO",
  "service": "bridge-v2",
  "batch_uid": "01939fd3-...",
  "entity": "items",
  "stage": "normalize",
  "message": "Normalized 1000 rows",
  "metrics": {
    "rows_normalized": 1000,
    "duration_ms": 250
  }
}
```

### Health Checks
- `GET /api/v1/health` - Service health
- `GET /api/v1/health/database` - Database connectivity
- `GET /api/v1/health/connector` - APISmith reachability
- `GET /api/v1/health/smartplan` - ScheduleHub reachability

---

## Development Workflow

### Setup
```bash
# Clone repo
cd bridge_v2/backend

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with credentials

# Run migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload --port 8008
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test
uv run pytest tests/test_normalization.py -v
```

### Code Quality
```bash
# Format code
uv run black app tests

# Lint
uv run ruff check app tests

# Type check
uv run mypy app
```

---

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete guide.

**Production Checklist**:
- [ ] Set strong `INTERNAL_SERVICE_JWT_SECRET`
- [ ] Configure production database credentials
- [ ] Enable TLS for all connections
- [ ] Set `DEBUG=False`
- [ ] Configure log rotation
- [ ] Setup monitoring (Prometheus + Grafana)
- [ ] Configure backup for PostgreSQL
- [ ] Test disaster recovery

---

## Related Documentation

- [DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md) - Database schema details
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Development roadmap
- [PROGRESS_LOG.md](./PROGRESS_LOG.md) - Session progress
- [API.md](./API.md) - API endpoints (TODO)
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide (TODO)

---

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review implementation plan
3. Check progress log for known issues
