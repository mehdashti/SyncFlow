# SyncFlow Implementation Plan

Based on [REQUIREMENTS.md](../../REQUIREMENTS.md) and [PHASE_2_SyncFlow_TASKS.md](/home/mahur/projects/Docs/PHASE_2_SyncFlow_TASKS.md)

## Timeline: Weeks 4-6 (Milestone M2)

---

## Week 4: Foundation & Normalization Engine

### ✅ Phase 4.0: Project Setup (COMPLETED)
- [x] Create project structure
- [x] Setup pyproject.toml with dependencies
- [x] Configure environment variables
- [x] Create database and user
- [x] Test basic FastAPI application

### 🔄 Phase 4.1: Database Schema & Core Models

#### Task 4.1.1: Database Connection Layer
**Priority**: P0 - Critical
**Files**:
- `app/db/__init__.py`
- `app/db/session.py`
- `app/db/base.py`

**Subtasks**:
- [ ] Create async SQLAlchemy engine
- [ ] Setup connection pooling
- [ ] Create async session factory
- [ ] Add connection health check
- [ ] Test database connectivity

#### Task 4.1.2: Create SQLAlchemy Models
**Priority**: P0 - Critical
**Files**:
- `app/models/__init__.py`
- `app/models/base.py`
- `app/models/batch.py` (SyncBatch, FailedRecord, PendingChild)
- `app/models/sync_state.py` (ERPSyncState, BackgroundSyncSchedule)
- `app/models/mapping.py` (FieldMapping)

**Schema Tables**:
1. `bridge.sync_batches` - Batch tracking
2. `bridge.failed_records` - Dead-letter queue
3. `bridge.pending_children` - Parent-child resolution queue
4. `bridge.erp_sync_state` - Delta detection state
5. `bridge.background_sync_schedule` - Background sync configuration
6. `bridge.field_mappings` - Field transformation rules

**Subtasks**:
- [ ] Create Base model with common fields
- [ ] Implement SyncBatch model
- [ ] Implement FailedRecord model
- [ ] Implement PendingChild model
- [ ] Implement ERPSyncState model
- [ ] Implement BackgroundSyncSchedule model
- [ ] Implement FieldMapping model
- [ ] Add all relationships and indexes

#### Task 4.1.3: Alembic Setup & Initial Migration
**Priority**: P0 - Critical
**Files**:
- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/001_initial_schema.py`

**Subtasks**:
- [ ] Configure Alembic for async operations
- [ ] Create initial migration with all 6 tables
- [ ] Test migration up/down
- [ ] Verify schema in database

---

### Phase 4.2: Normalization Engine (5 Layers)

#### Task 4.2.1: Layer 1 - Type Coercion
**Priority**: P0 - Critical
**File**: `app/services/normalization/layer_1_type_coercion.py`

**Subtasks**:
- [ ] Implement TypeCoercionLayer class
- [ ] Handle VARCHAR2, CHAR, CLOB → str
- [ ] Handle NUMBER → int/float/Decimal
- [ ] Handle DATE, TIMESTAMP → ISO string
- [ ] Handle RAW → hex string
- [ ] Handle NULL values
- [ ] Add error logging
- [ ] Write unit tests

#### Task 4.2.2: Layer 2 - String Normalization
**Priority**: P0 - Critical
**File**: `app/services/normalization/layer_2_string_normalization.py`

**Subtasks**:
- [ ] Implement StringNormalizationLayer class
- [ ] Trim whitespace
- [ ] Remove control characters
- [ ] Normalize line endings
- [ ] Handle encoding issues
- [ ] Convert empty strings to NULL
- [ ] Write unit tests

#### Task 4.2.3: Layer 3 - Numeric Normalization
**Priority**: P0 - Critical
**File**: `app/services/normalization/layer_3_numeric_normalization.py`

**Subtasks**:
- [ ] Implement NumericNormalizationLayer class
- [ ] Parse "10,000" → 10000
- [ ] Handle scientific notation
- [ ] Validate numeric ranges
- [ ] Null-safe parsing
- [ ] Write unit tests

#### Task 4.2.4: Layer 4 - Date/Time Normalization
**Priority**: P0 - Critical
**File**: `app/services/normalization/layer_4_datetime_normalization.py`

**Subtasks**:
- [ ] Implement DateTimeNormalizationLayer class
- [ ] Support multiple date formats (YYYY-MM-DD, YYYY/MM/DD, etc.)
- [ ] Handle Oracle DATE objects
- [ ] Convert to ISO 8601 format
- [ ] Handle timezone conversion
- [ ] Write unit tests

#### Task 4.2.5: Layer 5 - Field Mapping
**Priority**: P0 - Critical
**File**: `app/services/normalization/layer_5_field_mapping.py`

**Subtasks**:
- [ ] Implement FieldMappingLayer class
- [ ] Load mapping rules from database
- [ ] Apply field transformations
- [ ] Handle default values
- [ ] Validate required fields
- [ ] Write unit tests

#### Task 4.2.6: Normalization Engine Orchestrator
**Priority**: P0 - Critical
**File**: `app/services/normalization/engine.py`

**Subtasks**:
- [ ] Implement NormalizationEngine class
- [ ] Chain all 5 layers in sequence
- [ ] Add error handling per layer
- [ ] Track normalization metrics
- [ ] Write integration tests

---

### Phase 4.3: Repositories & Schemas

#### Task 4.3.1: Repository Layer
**Priority**: P1 - High
**Files**:
- `app/repositories/__init__.py`
- `app/repositories/batch_repository.py`
- `app/repositories/failed_record_repository.py`
- `app/repositories/sync_state_repository.py`
- `app/repositories/mapping_repository.py`

**Subtasks**:
- [ ] Implement BatchRepository (CRUD for sync_batches)
- [ ] Implement FailedRecordRepository
- [ ] Implement SyncStateRepository
- [ ] Implement MappingRepository
- [ ] Add async methods for all operations
- [ ] Write unit tests

#### Task 4.3.2: Pydantic Schemas
**Priority**: P1 - High
**Files**:
- `app/schemas/__init__.py`
- `app/schemas/batch.py`
- `app/schemas/sync.py`
- `app/schemas/mapping.py`

**Subtasks**:
- [ ] Create request/response schemas
- [ ] Add field validators
- [ ] Add JSON examples
- [ ] Document all fields

---

## Week 5: Identity & Delta Engines

### Phase 5.1: Identity Engine

#### Task 5.1.1: Business Key Hash (BK_HASH)
**Priority**: P0 - Critical
**File**: `app/services/identity/bk_hash.py`

**Subtasks**:
- [ ] Extract business key fields from metadata
- [ ] Create canonical string (field1=val1|field2=val2)
- [ ] Compute xxHash128 hash (32-char hex)
- [ ] Store in erp_key_hash field
- [ ] Write unit tests

#### Task 5.1.2: Data Hash (DATA_HASH)
**Priority**: P0 - Critical
**File**: `app/services/identity/data_hash.py`

**Subtasks**:
- [ ] Extract all data fields (sorted alphabetically)
- [ ] Create canonical string
- [ ] Compute BLAKE3 hash (64-char hex)
- [ ] Store in erp_data_hash field
- [ ] Write unit tests

#### Task 5.1.3: Rowversion Handler
**Priority**: P0 - Critical
**File**: `app/services/identity/rowversion.py`

**Subtasks**:
- [ ] Validate rowversion format
- [ ] Compare rowversion strings
- [ ] Store in erp_rowversion field
- [ ] Write unit tests

#### Task 5.1.4: Identity Engine Orchestrator
**Priority**: P0 - Critical
**File**: `app/services/identity/engine.py`

**Subtasks**:
- [ ] Implement IdentityEngine class
- [ ] Generate BK_HASH for all records
- [ ] Generate DATA_HASH for all records
- [ ] Extract rowversion if available
- [ ] Create erp_ref_str for debugging
- [ ] Write integration tests

---

### Phase 5.2: Delta Engine

#### Task 5.2.1: Delta Detection Logic
**Priority**: P0 - Critical
**File**: `app/services/delta/detector.py`

**Subtasks**:
- [ ] Implement DeltaDetector class
- [ ] Detect NEW records (BK_HASH not in ScheduleHub)
- [ ] Detect UPDATED records (rowversion or DATA_HASH changed)
- [ ] Detect DELETED records (BK_HASH missing from connector)
- [ ] Write unit tests

#### Task 5.2.2: Rowversion-based Delta
**Priority**: P0 - Critical
**File**: `app/services/delta/rowversion_strategy.py`

**Subtasks**:
- [ ] Compare incoming vs stored rowversion
- [ ] Mark as UPDATE if rowversion > stored
- [ ] Skip if rowversion unchanged
- [ ] Write unit tests

#### Task 5.2.3: Hash-based Delta
**Priority**: P0 - Critical
**File**: `app/services/delta/hash_strategy.py`

**Subtasks**:
- [ ] Compare incoming vs stored DATA_HASH
- [ ] Mark as UPDATE if hash differs
- [ ] Skip if hash unchanged
- [ ] Write unit tests

#### Task 5.2.4: Delta Engine Orchestrator
**Priority**: P0 - Critical
**File**: `app/services/delta/engine.py`

**Subtasks**:
- [ ] Implement DeltaEngine class
- [ ] Load existing records from ScheduleHub
- [ ] Apply delta detection strategy
- [ ] Return INSERT/UPDATE/DELETE lists
- [ ] Track delta metrics
- [ ] Write integration tests

---

### Phase 5.3: HTTP Clients

#### Task 5.3.1: APISmith Client
**Priority**: P0 - Critical
**File**: `app/services/connector_client/client.py`

**Subtasks**:
- [ ] Implement APISmithClient class
- [ ] Add JWT authentication
- [ ] Fetch connector list: GET /api/v1/connectors
- [ ] Fetch API list: GET /api/v1/apis
- [ ] Fetch data: POST /api/v1/runtime/{slug}/execute
- [ ] Handle pagination
- [ ] Add retry logic
- [ ] Write integration tests

#### Task 5.3.2: ScheduleHub Client
**Priority**: P0 - Critical
**File**: `app/services/smartplan_client/client.py`

**Subtasks**:
- [ ] Implement ScheduleHubClient class
- [ ] Add JWT authentication
- [ ] Check record exists: GET /api/v1/{entity}?filter={bk_hash}
- [ ] Insert record: POST /api/v1/{entity}
- [ ] Update record: PATCH /api/v1/{entity}/{uid}
- [ ] Batch operations
- [ ] Add retry logic
- [ ] Write integration tests

---

## Week 6: Parent-Child & Background Sync

### Phase 6.1: Parent-Child Resolver

#### Task 6.1.1: Dependency Detector
**Priority**: P0 - Critical
**File**: `app/services/parent_child/detector.py`

**Subtasks**:
- [ ] Define parent-child relationships config
- [ ] Detect missing parent for child record
- [ ] Store in pending_children table
- [ ] Write unit tests

#### Task 6.1.2: Retry Mechanism
**Priority**: P0 - Critical
**File**: `app/services/parent_child/retry.py`

**Subtasks**:
- [ ] Query pending_children periodically
- [ ] Check if parent now exists
- [ ] Retry child ingestion
- [ ] Exponential backoff
- [ ] Max retry limit (5 attempts)
- [ ] Write unit tests

#### Task 6.1.3: Parent-Child Resolver Engine
**Priority**: P0 - Critical
**File**: `app/services/parent_child/engine.py`

**Subtasks**:
- [ ] Implement ParentChildResolver class
- [ ] Detect dependencies
- [ ] Queue pending children
- [ ] Resolve when parent arrives
- [ ] Track resolution metrics
- [ ] Write integration tests

---

### Phase 6.2: Background Sync Scheduler

#### Task 6.2.1: Scheduler Configuration
**Priority**: P1 - High
**File**: `app/services/batch/scheduler.py`

**Subtasks**:
- [ ] Setup APScheduler
- [ ] Load schedules from background_sync_schedule table
- [ ] Enforce time window (19:00 - 07:00)
- [ ] Compute daily offsets for 7-day sync
- [ ] Write unit tests

#### Task 6.2.2: Background Sync Executor
**Priority**: P1 - High
**File**: `app/services/batch/background_sync.py`

**Subtasks**:
- [ ] Fetch batch from APISmith (with offset/limit)
- [ ] Process through full pipeline
- [ ] Update current_offset
- [ ] Schedule next day's batch
- [ ] Write integration tests

---

### Phase 6.3: Batch Orchestrator

#### Task 6.3.1: Sync Job Orchestrator
**Priority**: P0 - Critical
**File**: `app/services/batch/orchestrator.py`

**Subtasks**:
- [ ] Implement BatchOrchestrator class
- [ ] Create sync_batch record
- [ ] Fetch data from APISmith
- [ ] Run normalization pipeline
- [ ] Run identity engine
- [ ] Run delta engine
- [ ] Resolve parent-child
- [ ] Send to ScheduleHub
- [ ] Handle errors → failed_records
- [ ] Update sync_batch metrics
- [ ] Write integration tests

---

### Phase 6.4: API Routes

#### Task 6.4.1: Sync Management Routes
**Priority**: P1 - High
**File**: `app/routers/sync.py`

**Endpoints**:
- [ ] POST /api/v1/sync/start - Start sync for entity
- [ ] GET /api/v1/sync/status/{batch_uid} - Get batch status
- [ ] POST /api/v1/sync/stop/{batch_uid} - Stop running sync
- [ ] GET /api/v1/sync/history - Get sync history
- [ ] POST /api/v1/sync/retry-failed - Retry failed records

#### Task 6.4.2: Entity Management Routes
**Priority**: P1 - High
**File**: `app/routers/entities.py`

**Endpoints**:
- [ ] GET /api/v1/entities - List configured entities
- [ ] POST /api/v1/entities - Add entity configuration
- [ ] GET /api/v1/entities/{uid} - Get entity details
- [ ] PUT /api/v1/entities/{uid} - Update entity config
- [ ] DELETE /api/v1/entities/{uid} - Delete entity

#### Task 6.4.3: Monitoring Routes
**Priority**: P2 - Medium
**File**: `app/routers/monitoring.py`

**Endpoints**:
- [ ] GET /api/v1/metrics - Prometheus metrics
- [ ] GET /api/v1/stats - Sync statistics
- [ ] GET /api/v1/failed-records - List failed records
- [ ] GET /api/v1/pending-children - List pending children

---

## Week 6: Testing & Documentation

### Phase 6.5: Testing

#### Task 6.5.1: Unit Tests
- [ ] Test all normalization layers
- [ ] Test identity engine
- [ ] Test delta engine
- [ ] Test parent-child resolver
- [ ] Achieve >80% code coverage

#### Task 6.5.2: Integration Tests
- [ ] Test full sync flow (APISmith → SyncFlow → ScheduleHub)
- [ ] Test error handling
- [ ] Test retry logic
- [ ] Test background sync

#### Task 6.5.3: Load Tests
- [ ] Test 1M rows sync performance
- [ ] Test concurrent syncs
- [ ] Validate performance targets (<10s for 1M rows)

---

### Phase 6.6: Documentation

#### Task 6.6.1: API Documentation
- [ ] Complete OpenAPI schema
- [ ] Add examples for all endpoints
- [ ] Document error responses

#### Task 6.6.2: Architecture Documentation
- [ ] Document 9-stage pipeline
- [ ] Document delta strategies
- [ ] Document parent-child resolution
- [ ] Add sequence diagrams

---

## Milestone M2: Acceptance Criteria

### Must Have
- [ ] All 6 database tables created
- [ ] 5-layer normalization working
- [ ] BK_HASH + DATA_HASH generation
- [ ] Delta detection (INSERT/UPDATE/DELETE)
- [ ] Parent-child resolution
- [ ] Batch orchestration working
- [ ] Failed records captured
- [ ] Sync metrics tracked
- [ ] API endpoints operational
- [ ] Basic tests passing

### Performance Targets
- [ ] 1M rows processed in <10 seconds
- [ ] Delta sync accuracy: 100%
- [ ] Parent-child resolution: 100%
- [ ] Error rate: <0.2%

---

## Next Steps

After M2 completion, proceed to **ScheduleHub** (Weeks 7-9).
