# Architecture Standards for SyncFlow

**Date:** 2025-12-18
**Scope:** Mandatory standards for SyncFlow (Bridge) microservice.
**Inherits From:** `/home/mahur/Desktop/Projects/APISmith/ARCHITECTURE_STANDARDS.md`

## 0. Check Before Code Principle

**CRITICAL: Always verify before implementing new functionality.**

Before writing any new code:

1. **Search for existing implementations**
   - Use `grep` or IDE search to find similar functions/classes
   - Check the same domain/feature area for related code
   - Look for similar patterns in other microservices (APISmith, ScheduleHub)

2. **Verify type definitions**
   - Check `app/schemas/` for existing Pydantic models
   - Review `app/db/base.py` for table definitions
   - Ensure new types don't duplicate existing ones

3. **Review repository layer**
   - Check `app/repositories/` for existing database operations
   - Verify if similar queries already exist
   - Don't duplicate CRUD operations

4. **Check API routes**
   - Review `app/routers/` for existing endpoints
   - Avoid duplicate HTTP handlers
   - Ensure consistent URL patterns

5. **Examine service layer**
   - Review `app/services/` for business logic
   - Check if similar operations exist in different services
   - Avoid reimplementing existing functionality

6. **Dependencies and utilities**
   - Check `app/core/` for existing utilities (uuid_utils, exceptions, etc.)
   - Review `pyproject.toml` before adding new dependencies
   - Use existing helper functions

**Rationale:** This prevents code duplication, maintains consistency across the codebase, and ensures we build on existing patterns rather than creating conflicting implementations.

---

## 1. SyncFlow-Specific Principles

All standards from APISmith apply, plus:

1. **Delta Strategies:** Support three strategies: `full`, `rowversion`, `hash`
2. **Business Keys:** Must be configurable per entity (stored in `entity_config.business_key_fields`)
3. **5-Layer Normalization:** Always process data through all layers (type coercion → string → numeric → datetime → field mapping)
4. **Identity Engine:** Generate both `BK_HASH` (business key hash) and `DATA_HASH` (data hash) for delta detection
5. **Parent-Child Resolution:** Queue children with missing parents in `pending_children` table
6. **Background Sync:** Enforce time window (19:00-07:00) with multi-day batch processing
7. **Dynamic Tables:** SyncFlow creates tables in ScheduleHub with `_bridge_*` columns for tracking

---

## 2. File Structure (Inherited + Extended)

```
SyncFlow/backend/
├── app/
│   ├── api/              # (future: deps, error handlers)
│   ├── core/
│   │   ├── config.py     # ✅ Settings with APISmith/ScheduleHub URLs
│   │   ├── uuid_utils.py # ⚠️ MISSING - Must add for UUID v7 generation
│   │   ├── exceptions.py # ⚠️ MISSING - Standard exceptions
│   │   └── logging.py    # ✅ Structured logging
│   ├── db/
│   │   ├── base.py       # ✅ 7 metadata tables defined
│   │   └── session.py    # ✅ Async engine
│   ├── repositories/     # ✅ All 6 repositories exist
│   ├── routers/          # ✅ All 5 routers exist
│   ├── schemas/          # ✅ Pydantic models
│   └── services/
│       ├── connector_client/   # ✅ APISmith HTTP client
│       ├── smartplan_client/   # ✅ ScheduleHub HTTP client
│       ├── normalization/      # ✅ 5 layers + engine
│       ├── identity/           # ✅ BK_HASH + DATA_HASH + rowversion
│       ├── delta/              # ✅ Detection strategies
│       ├── resolver/           # ✅ Parent-child resolution
│       ├── orchestrator/       # ✅ Main sync pipeline
│       └── scheduler/          # ✅ Background sync scheduler
├── scripts/
│   └── init_db.py        # ⚠️ May need Alembic setup
├── tests/                # ⚠️ Coverage needed
└── alembic/              # ⚠️ Migrations needed
```

---

## 3. Required Core Modules

### ✅ Already Implemented
- `app/core/config.py` - Settings with APISmith/ScheduleHub integration
- `app/core/logging.py` - Structured logging
- `app/db/base.py` - 7 metadata tables (sync_batches, failed_records, pending_children, etc.)
- `app/db/session.py` - Async engine

### ⚠️ Missing (Must Add)
- `app/core/uuid_utils.py` - Must provide `generate_uuid7()` function
- `app/core/exceptions.py` - Standard exceptions (AlreadyExistsError, NotFoundError, etc.)
- Alembic migrations for the 7 metadata tables

---

## 4. Repository Pattern (Inherited)

Same as APISmith:
- Generate UUIDs in Python with `generate_uuid7()`
- Return dict payloads with `row._mapping`
- Provide async `create`, `get_by_uid`, `update`, `delete` methods

---

## 5. Service Layer Specifics

### 5.1 Normalization Pipeline
All data must flow through 5 layers sequentially:
1. Type Coercion (Oracle types → Python types)
2. String Normalization (trim, encoding, control chars)
3. Numeric Normalization (parse "10,000" → 10000)
4. DateTime Normalization (multiple formats → ISO 8601)
5. Field Mapping (apply transformations from `field_mappings` table)

### 5.2 Identity Engine
Generate for every record:
- `erp_key_hash` (BK_HASH): xxHash128 of business keys
- `erp_data_hash` (DATA_HASH): BLAKE3 of all data fields
- `erp_rowversion`: Extracted if available
- `erp_ref_str`: Human-readable debug string

### 5.3 Delta Engine
Support three strategies:
- **Full**: All records are INSERTS (no delta detection)
- **Rowversion**: Compare `erp_rowversion` with stored value
- **Hash**: Compare `erp_data_hash` with stored value

### 5.4 Parent-Child Resolver
- Detect missing parent references from `entity_config.parent_refs_config`
- Queue children in `pending_children` table
- Retry with exponential backoff (max 5 attempts)
- Resolve when parent arrives

### 5.5 Background Sync Scheduler
- Load schedules from `background_sync_schedule` table
- Enforce time window: 19:00-07:00
- Split large datasets across `days_to_complete` (default 7 days)
- Track `current_offset` for resumability

---

## 6. API Routes

All routes under `/api/v1`:

- **Connectors** (`/connectors`)
  - GET, POST, PATCH, DELETE
  - Manage APISmith connector configurations

- **Entities** (`/entities`)
  - GET, POST, PATCH, DELETE
  - Configure business keys, delta strategy, parent refs

- **Sync** (`/sync`)
  - POST `/sync/start` - Start realtime sync
  - GET `/sync/status/{batch_uid}` - Check batch status
  - POST `/sync/stop/{batch_uid}` - Cancel running sync
  - GET `/sync/history` - List sync batches

- **Schedules** (`/schedules`)
  - GET, POST, PATCH, DELETE
  - Manage background sync schedules

- **Monitoring** (`/monitoring`)
  - GET `/failed-records` - List failed records
  - GET `/pending-children` - List pending children
  - GET `/stats` - Sync statistics
  - GET `/metrics` - Prometheus metrics

---

## 7. Security Standards (Inherited)

Same as APISmith:
- Argon2id for password hashing
- AES-256-GCM for sensitive data
- JWT tokens for APISmith/ScheduleHub communication
- Never commit secrets to code

---

## 8. Testing Strategy

### Unit Tests
- All normalization layers (5 layers)
- Identity engine (BK_HASH, DATA_HASH)
- Delta strategies (full, rowversion, hash)
- Parent-child resolver

### Integration Tests
- Full pipeline: APISmith → Normalization → Identity → Delta → ScheduleHub
- Error handling and failed_records
- Retry logic for failed records and pending children

### Load Tests
- Process 1M rows in <10 seconds
- Concurrent syncs
- Background sync performance

Target: >80% code coverage

---

## 9. Observability (Inherited)

- Structured JSON logging with correlation IDs
- Prometheus metrics for sync performance
- Health endpoints: `/api/v1/health`, `/api/v1/health/detailed`
- Track metrics per batch: rows_fetched, rows_normalized, rows_inserted, etc.

---

## 10. Operational Scripts

Provide:
- `setup.sh` - Environment setup and dependency sync
- `scripts/init_db.py` - Database initialization
- Alembic migrations for schema versioning

---

This document extends the APISmith architecture standards with SyncFlow-specific requirements. Always follow the "Check Before Code" principle before implementing new features.
