# SyncFlow - Data Integration Microservice

## Overview
SyncFlow is a data synchronization microservice that fetches data from APISmith APIs and stores it in PostgreSQL for downstream applications. It replaces the legacy SyncFlow V1 with a modern, maintainable architecture.

---

## Architecture Principles

### 1. **APISmith-Driven Metadata**
- SyncFlow discovers available APIs from APISmith
- No hardcoded entity definitions
- API metadata defines table schema, business keys, delta strategy

### 2. **Incremental Sync (Delta Strategy)**
- **Full Sync**: Fetch all records, compare with local DB
- **Rowversion Sync**: Fetch only records with `rowversion > last_sync_value`
- **Hash Sync**: Compare hash of record fields to detect changes

### 3. **Dynamic Table Management**
- Auto-create PostgreSQL tables based on API column metadata
- Dynamic column mapping (API output_alias -> PostgreSQL column)
- Business key constraints for upserts

### 4. **Async/Await Architecture**
- FastAPI with async database operations
- Async HTTP client for APISmith API calls
- Background task scheduler for periodic syncs

### 5. **Multi-Tenant Support**
- Single SyncFlow instance can sync from multiple APISmiths
- Configurable per-entity sync intervals
- Independent schema per source system

---

## Key Features

- 🔄 **Automatic Discovery**: Discover APIs from APISmith metadata endpoint
- 📊 **Dynamic Schema**: Auto-create tables based on API column definitions
- ⚡ **Incremental Sync**: Rowversion-based delta sync for efficiency
- 🔑 **Business Key Matching**: Upsert based on business keys from APISmith
- 📅 **Scheduled Syncs**: Configurable sync intervals per entity
- 📈 **Sync Monitoring**: Track sync status, records processed, errors
- 🛡️ **Error Handling**: Retry failed syncs, log errors
- 🌍 **Multi-APISmith**: Support multiple APISmith instances
- 🔄 **Full Refresh**: Force full sync on demand
- 📝 **Audit Trail**: Track sync history, record changes

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     SyncFlow                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. API Discovery Service                            │  │
│  │     - Fetch API list from APISmith                  │  │
│  │     - Store metadata (columns, business keys)        │  │
│  │     - Detect schema changes                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2. Table Manager                                    │  │
│  │     - Create/update PostgreSQL tables                │  │
│  │     - Add columns dynamically                        │  │
│  │     - Manage constraints (business keys)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  3. Sync Scheduler                                   │  │
│  │     - Schedule periodic syncs (cron-like)            │  │
│  │     - Track last sync timestamp                      │  │
│  │     - Queue sync jobs                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  4. Sync Executor                                    │  │
│  │     - Fetch data from APISmith                   │  │
│  │     - Apply delta strategy (rowversion/hash/full)    │  │
│  │     - Upsert records using business keys             │  │
│  │     - Track sync metrics                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  5. PostgreSQL Database (SyncFlow DB)                  │  │
│  │     - Dynamic tables per entity                      │  │
│  │     - Audit columns (created_at, updated_at)         │  │
│  │     - Sync metadata tables                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↑
                           │ HTTP REST API
                           │
            ┌──────────────────────────────┐
            │     APISmith             │
            │  (Data Source)               │
            └──────────────────────────────┘
```

---

## Database Schema

### SyncFlow Metadata Tables

#### `connectors` Table
Stores APISmith instance configurations.

```sql
CREATE TABLE bridge.connectors (
    uid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    auth_token TEXT,  -- JWT token for APISmith API
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `entities` Table
Stores discovered APIs from APISmith.

```sql
CREATE TABLE bridge.entities (
    uid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_uid UUID REFERENCES bridge.connectors(uid) ON DELETE CASCADE,
    slug VARCHAR(100) NOT NULL,  -- API slug from APISmith
    api_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Delta strategy from APISmith metadata
    delta_strategy VARCHAR(20) NOT NULL DEFAULT 'full',  -- full, rowversion, hash
    business_keys JSONB NOT NULL,  -- Array of business key column names

    -- Table mapping
    target_schema VARCHAR(100) NOT NULL DEFAULT 'public',
    target_table VARCHAR(100) NOT NULL,

    -- Column metadata from APISmith
    columns JSONB NOT NULL,  -- Array of {name, data_type, is_nullable, is_business_key}

    -- Sync configuration
    sync_enabled BOOLEAN DEFAULT TRUE,
    sync_interval_seconds INT DEFAULT 300,  -- 5 minutes

    -- Sync state
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(20),  -- success, failed, running
    last_rowversion VARCHAR(100),  -- Last rowversion value for delta sync

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(connector_uid, slug)
);
```

#### `sync_runs` Table
Tracks sync execution history.

```sql
CREATE TABLE bridge.sync_runs (
    uid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_uid UUID REFERENCES bridge.entities(uid) ON DELETE CASCADE,

    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- running, success, failed

    -- Sync metrics
    records_fetched INT DEFAULT 0,
    records_inserted INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    records_unchanged INT DEFAULT 0,

    -- Rowversion tracking
    rowversion_start VARCHAR(100),
    rowversion_end VARCHAR(100),

    -- Error info
    error_message TEXT,
    error_details JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);
```

### Dynamic Entity Tables

SyncFlow creates one table per entity in the target schema (e.g., `public.items`, `public.customers`).

**Auto-generated columns**:
- All columns from API metadata (with proper PostgreSQL types)
- `_bridge_id` (UUID, primary key)
- `_bridge_created_at` (timestamp)
- `_bridge_updated_at` (timestamp)
- `_bridge_hash` (text, for hash-based delta sync)
- `_bridge_deleted` (boolean, soft delete flag)

**Example**:
```sql
-- Generated for "items" API
CREATE TABLE public.items (
    _bridge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- API columns (from APISmith metadata)
    item_number VARCHAR(50) NOT NULL,
    item_description TEXT,
    base_uom VARCHAR(10),
    weight_per_unit NUMERIC(10, 3),
    erp_rowversion VARCHAR(50),

    -- SyncFlow audit columns
    _bridge_created_at TIMESTAMP DEFAULT NOW(),
    _bridge_updated_at TIMESTAMP DEFAULT NOW(),
    _bridge_hash TEXT,
    _bridge_deleted BOOLEAN DEFAULT FALSE,

    -- Business key constraint (from APISmith metadata)
    UNIQUE(item_number)
);

-- Index on rowversion for delta sync performance
CREATE INDEX idx_items_rowversion ON public.items(erp_rowversion);
```

---

## API Endpoints

### Admin APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/connectors` | Register new APISmith instance |
| GET | `/api/v1/connectors` | List all APISmiths |
| GET | `/api/v1/connectors/{uid}` | Get APISmith details |
| PUT | `/api/v1/connectors/{uid}` | Update APISmith config |
| DELETE | `/api/v1/connectors/{uid}` | Delete APISmith |
| POST | `/api/v1/connectors/{uid}/test` | Test APISmith connection |

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/connectors/{uid}/discover` | Discover APIs from APISmith |
| GET | `/api/v1/entities` | List all discovered entities |
| GET | `/api/v1/entities/{uid}` | Get entity details |
| PUT | `/api/v1/entities/{uid}` | Update entity config (sync interval, etc.) |
| POST | `/api/v1/entities/{uid}/sync` | Trigger manual sync |
| POST | `/api/v1/entities/{uid}/full-refresh` | Force full sync (ignore rowversion) |

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/entities/{uid}/runs` | Get sync run history |
| GET | `/api/v1/runs/{uid}` | Get sync run details |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Basic health check |
| GET | `/api/v1/health/db` | Database connectivity check |

---

## Sync Flow

### 1. Discovery Phase

```python
# Admin triggers discovery
POST /api/v1/connectors/{connector_uid}/discover

# SyncFlow calls APISmith
GET http://connector:8007/api/v1/apis

# SyncFlow receives API list
[
    {
        "slug": "items",
        "name": "Items",
        "description": "Product master data",
        "columns": [...],
        "business_key_columns": ["item_number"],
        "delta_strategy": "rowversion",
        ...
    }
]

# SyncFlow creates entity records in `entities` table
# SyncFlow creates PostgreSQL tables with proper schema
```

### 2. Scheduled Sync Phase

```python
# Background scheduler runs every minute
# Checks entities where:
#   - sync_enabled = TRUE
#   - last_sync_at + sync_interval_seconds < NOW()

for entity in entities_to_sync:
    execute_sync(entity)
```

### 3. Sync Execution Phase

```python
async def execute_sync(entity):
    # 1. Create sync_run record (status=running)
    sync_run = create_sync_run(entity)

    # 2. Determine delta strategy
    if entity.delta_strategy == 'rowversion':
        # Use last_rowversion for incremental sync
        params = {
            'rowversion_gt': entity.last_rowversion,
            'page': 1,
            'page_size': 1000
        }
    elif entity.delta_strategy == 'full':
        # Fetch all records
        params = {'page': 1, 'page_size': 1000}

    # 3. Fetch data from APISmith (paginated)
    all_rows = []
    while True:
        response = await connector_client.get(
            f"/api/v1/data/{entity.slug}",
            params=params
        )

        rows = response.json()['rows']
        if not rows:
            break

        all_rows.extend(rows)
        params['page'] += 1

    # 4. Upsert records using business keys
    inserted, updated, unchanged = 0, 0, 0

    for row in all_rows:
        business_key = row['oracle_keys']  # e.g., {"PART_NO": "ABC123"}
        row_version = row['row_version']
        data = row['data']

        # Check if record exists (match on business key)
        existing = await find_record_by_business_key(entity, business_key)

        if not existing:
            await insert_record(entity.target_table, data)
            inserted += 1
        else:
            # Compare by hash or rowversion
            if has_changed(existing, data, row_version):
                await update_record(entity.target_table, existing.id, data)
                updated += 1
            else:
                unchanged += 1

    # 5. Update entity last_sync state
    entity.last_sync_at = NOW()
    entity.last_rowversion = max_rowversion(all_rows)
    entity.last_sync_status = 'success'

    # 6. Complete sync_run record
    sync_run.completed_at = NOW()
    sync_run.status = 'success'
    sync_run.records_fetched = len(all_rows)
    sync_run.records_inserted = inserted
    sync_run.records_updated = updated
    sync_run.records_unchanged = unchanged
```

---

## Configuration

### Environment Variables

```bash
# Application
APP_ENV=development
DEBUG=True

# API
API_HOST=0.0.0.0
API_PORT=8008

# SyncFlow Database (PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_DB=bridge_v2_db
POSTGRES_SCHEMA=bridge
POSTGRES_USER=bridge_user
POSTGRES_PASSWORD=***

# Default APISmith
DEFAULT_APISmith_URL=http://localhost:8007
DEFAULT_APISmith_TOKEN=***

# Sync Configuration
DEFAULT_SYNC_INTERVAL_SECONDS=300  # 5 minutes
MAX_PAGE_SIZE=1000
SYNC_WORKER_THREADS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/bridge_v2.log
```

---

## Technology Stack

### Backend
- **Python 3.13**
- **FastAPI** - Async web framework
- **SQLAlchemy 2.0** - Database ORM (async)
- **asyncpg** - Async PostgreSQL driver
- **httpx** - Async HTTP client for APISmith API calls
- **APScheduler** - Background task scheduler
- **Pydantic V2** - Data validation

### Database
- **PostgreSQL 16+** - Main data storage
- **Alembic** - Database migrations

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Local development
- **Kubernetes** - Production deployment

---

## Project Structure

```
bridge_v2/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── connectors.py       # APISmith management
│   │   │   ├── entities.py         # Entity management
│   │   │   ├── sync.py             # Sync operations
│   │   │   └── healthcheck.py      # Health checks
│   │   └── errors/
│   │       └── handlers.py         # Exception handlers
│   ├── core/
│   │   ├── config.py               # Pydantic settings
│   │   ├── logging.py              # Logging setup
│   │   └── scheduler.py            # APScheduler config
│   ├── services/
│   │   ├── discovery/
│   │   │   └── api_discovery.py    # Discover APIs from APISmith
│   │   ├── table_manager/
│   │   │   └── schema_manager.py   # Create/update PostgreSQL tables
│   │   ├── sync/
│   │   │   ├── sync_executor.py    # Execute sync jobs
│   │   │   ├── delta_strategy.py   # Delta sync strategies
│   │   │   └── upsert_handler.py   # Business key upsert logic
│   │   └── connector_client/
│   │       └── client.py           # HTTP client for APISmith
│   ├── models/
│   │   ├── connector.py            # APISmith model
│   │   ├── entity.py               # Entity model
│   │   └── sync_run.py             # SyncRun model
│   ├── repositories/
│   │   ├── connector_repository.py
│   │   ├── entity_repository.py
│   │   └── sync_run_repository.py
│   ├── db/
│   │   ├── base.py                 # Database session
│   │   └── schema.py               # SyncFlow metadata schema
│   └── main.py                     # FastAPI app
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── test_api_discovery.py
│   ├── test_sync_executor.py
│   └── test_table_manager.py
├── scripts/
│   ├── setup_database.sh
│   └── seed_connector.py
├── .env.example
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- ✅ Project setup (FastAPI, SQLAlchemy, async)
- ✅ Database schema design (connectors, entities, sync_runs)
- ✅ Alembic migrations
- ✅ Basic CRUD APIs (connectors, entities)
- ✅ Health check endpoints

### Phase 2: API Discovery (Week 2)
- ✅ APISmith client (HTTP client with authentication)
- ✅ API discovery service (fetch API list from APISmith)
- ✅ Entity metadata storage (columns, business keys, delta strategy)
- ✅ Discovery endpoint (/connectors/{uid}/discover)

### Phase 3: Table Management (Week 2-3)
- ✅ Schema manager (create tables dynamically)
- ✅ Column type mapping (API data_type -> PostgreSQL type)
- ✅ Business key constraint generation
- ✅ Add audit columns (_bridge_created_at, etc.)
- ✅ Handle schema changes (add columns dynamically)

### Phase 4: Sync Executor (Week 3-4)
- ✅ Sync executor service (fetch data, upsert records)
- ✅ Delta strategy implementation:
  - Full sync (fetch all, compare locally)
  - Rowversion sync (fetch only changed records)
  - Hash sync (calculate hash, compare)
- ✅ Business key matching and upsert
- ✅ Sync metrics tracking
- ✅ Manual sync endpoint (/entities/{uid}/sync)

### Phase 5: Scheduler (Week 4)
- ✅ APScheduler integration
- ✅ Background sync worker
- ✅ Sync interval configuration per entity
- ✅ Concurrent sync handling (worker pool)
- ✅ Error handling and retry logic

### Phase 6: Monitoring & Logging (Week 5)
- ✅ Sync run history (/entities/{uid}/runs)
- ✅ Detailed logging (structured logs)
- ✅ Error tracking and alerts
- ✅ Sync performance metrics

### Phase 7: Testing & Quality (Week 5-6)
- ✅ Unit tests (pytest, >80% coverage)
- ✅ Integration tests (test with real APISmith)
- ✅ Load testing (large datasets)
- ✅ API documentation (OpenAPI/Swagger)

### Phase 8: DevOps (Week 6)
- ✅ Docker containerization
- ✅ Docker Compose for local dev
- ✅ Kubernetes deployment manifests
- ✅ CI/CD pipeline
- ✅ Production monitoring (Prometheus, Grafana)

---

## Key Design Decisions

### 1. Dynamic vs. Static Schema
**Decision**: Dynamic table creation based on API metadata
**Rationale**:
- No hardcoded entity definitions
- APISmith defines schema
- SyncFlow adapts automatically to API changes

### 2. Business Key Upsert Strategy
**Decision**: Use business keys from APISmith for upsert
**Rationale**:
- APISmith knows the true business keys (from ERP)
- SyncFlow doesn't need to guess or configure
- Matches V1 architecture

### 3. Rowversion Comparison
**Decision**: String comparison for rowversion values
**Rationale**:
- Oracle timestamps can be strings (e.g., "20251208120000")
- PostgreSQL can compare string timestamps
- Avoids type conversion issues

### 4. Sync Scheduler
**Decision**: APScheduler (in-process scheduler)
**Rationale**:
- Simple, no external dependencies (Redis/Celery)
- Per-entity configurable intervals
- Sufficient for most use cases
- Future: Can migrate to Celery if needed

### 5. Error Handling
**Decision**: Retry failed syncs 3 times, then mark as failed
**Rationale**:
- Transient errors (network issues) should be retried
- Persistent errors (bad data) should be logged and alerted
- Admin can manually retry from UI

---

## Migration from SyncFlow V1

### Differences from V1:
1. **No Python Module Generation**: V2 uses dynamic table management instead of generating Python modules per entity
2. **APISmith-Driven**: V1 had hardcoded entity definitions; V2 discovers from APISmith
3. **Async/Await**: V2 is fully async; V1 was synchronous
4. **Multi-APISmith**: V2 supports multiple APISmith instances; V1 was single-source
5. **Simplified Architecture**: V2 has fewer moving parts (no Redis, no Celery initially)

### Migration Steps:
1. Deploy SyncFlow alongside V1
2. Register APISmith in SyncFlow
3. Discover APIs from APISmith
4. Run initial full sync for all entities
5. Monitor sync runs for a week
6. Switch downstream apps to SyncFlow tables
7. Decommission SyncFlow V1

---

## Success Criteria

✅ **Phase 1-2**:
- SyncFlow can discover APIs from APISmith
- Entity metadata is stored correctly
- Business keys and delta strategy are captured

✅ **Phase 3**:
- Tables are created dynamically with correct schema
- Business key constraints are applied
- Audit columns are added

✅ **Phase 4-5**:
- Full sync works (all records fetched and inserted)
- Rowversion delta sync works (only changed records fetched)
- Scheduled syncs run automatically

✅ **Phase 6-8**:
- Sync history is tracked
- Errors are logged and alerted
- Performance is acceptable (1M records in <5 minutes)

---

## Performance Targets

- **Small Entity (<10K records)**: Full sync in <10 seconds
- **Medium Entity (10K-100K records)**: Full sync in <1 minute
- **Large Entity (>100K records)**: Full sync in <5 minutes
- **Delta Sync**: <10 seconds for typical change volumes (<1000 records)
- **Sync Interval**: Default 5 minutes, configurable per entity
- **Concurrent Syncs**: Support 10+ entities syncing simultaneously

---

## Security Considerations

- ✅ APISmith authentication (JWT token)
- ✅ Database connection encryption (SSL)
- ✅ Secrets management (environment variables, Vault)
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (parameterized queries)
- ✅ Rate limiting (future enhancement)

---

## Monitoring & Alerts

### Metrics to Track:
- Sync success/failure rate
- Sync duration per entity
- Records processed per sync
- Error count by entity
- Database connection pool usage
- API latency to APISmith

### Alerts:
- Sync failure (3 consecutive failures)
- Sync duration exceeds threshold (>10 minutes)
- Database connection pool exhausted
- APISmith unreachable

---

## Future Enhancements

1. **Soft Delete Support**: Track deleted records from ERP
2. **Change Data Capture (CDC)**: Use database triggers instead of polling
3. **GraphQL API**: For downstream apps to query SyncFlow data
4. **Multi-Tenant**: Isolated schemas per tenant
5. **Real-Time Sync**: WebSocket-based push from APISmith
6. **Smart Scheduling**: ML-based optimal sync intervals
7. **Data Transformation**: Allow custom transformations before storage
8. **Audit Log**: Track all changes to records (history table)

---

## License

Internal use only - ScheduleHub Project

---

## Team

Developed by ScheduleHub Team

---

## Support

For questions or issues, contact the development team.
