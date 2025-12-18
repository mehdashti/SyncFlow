# SyncFlow - Data Integration Microservice

**Version:** 2.0.0
**Status:** ✅ Production Ready
**Architecture:** APISmith → SyncFlow (Bridge) → ScheduleHub

---

## 📋 Overview

SyncFlow is the **middleware integration service** that orchestrates data synchronization between APISmith (connector layer) and ScheduleHub (planning engine). It handles:

- **5-Layer Normalization** of raw ERP data
- **Identity Generation** (BK_HASH, DATA_HASH) for delta detection
- **Delta Strategies** (full, rowversion, hash-based)
- **Parent-Child Resolution** with automatic retry
- **Background Sync Scheduler** with time windows
- **Failed Records Queue** for error recovery

---

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│  APISmith   │────────▶│   SyncFlow   │────────▶│ ScheduleHub  │
│  (Oracle    │         │   (Bridge)   │         │  (Planning)  │
│   ERP)      │         │              │         │              │
└─────────────┘         └──────────────┘         └──────────────┘
      │                        │                         │
      │                        │                         │
   Connector              Normalization             Scheduling
   Metadata              Identity + Delta           Engine
```

### 9-Stage Pipeline:

1. **Fetch** - Get data from APISmith
2. **Type Coercion** - Oracle types → Python types
3. **String Normalization** - Trim, encoding, control chars
4. **Numeric Normalization** - Parse "10,000" → 10000
5. **DateTime Normalization** - Multiple formats → ISO 8601
6. **Field Mapping** - Apply transformations
7. **Identity Generation** - BK_HASH + DATA_HASH
8. **Delta Detection** - Determine INSERT/UPDATE/DELETE
9. **Load** - Send to ScheduleHub

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- UV package manager
- PostgreSQL 14+
- APISmith running on port 8007
- ScheduleHub running on port 5180

### Installation

```bash
# Clone repository
cd /home/mahur/Desktop/Projects/SyncFlow/backend

# Install dependencies with UV
uv sync

# Configure environment
cp .env.example .env
nano .env  # Update database credentials

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --host 127.0.0.1 --port 8008
```

### Frontend Setup

```bash
cd /home/mahur/Desktop/Projects/SyncFlow/frontend

# Install dependencies
pnpm install

# Start development server
pnpm run dev  # Runs on port 3008
```

---

## 📁 Project Structure

```
SyncFlow/
├── backend/
│   ├── app/
│   │   ├── api/                    # API dependencies
│   │   ├── core/                   # Config, logging, uuid_utils, exceptions
│   │   ├── db/                     # Database schema (7 metadata tables)
│   │   ├── repositories/           # Data access layer (SQLAlchemy Core)
│   │   ├── routers/                # FastAPI routes
│   │   ├── schemas/                # Pydantic models
│   │   └── services/
│   │       ├── normalization/      # 5-layer normalization
│   │       ├── identity/           # BK_HASH + DATA_HASH
│   │       ├── delta/              # Delta detection strategies
│   │       ├── resolver/           # Parent-child resolver
│   │       ├── orchestrator/       # Main sync pipeline
│   │       ├── scheduler/          # Background sync
│   │       ├── connector_client/   # APISmith HTTP client
│   │       └── smartplan_client/   # ScheduleHub HTTP client
│   ├── tests/                      # 93+ unit + integration tests
│   ├── alembic/                    # Database migrations
│   └── pyproject.toml              # UV dependencies
├── frontend/
│   ├── src/
│   │   ├── api/                    # API services
│   │   ├── components/             # shadcn/ui components
│   │   ├── features/               # Feature modules
│   │   ├── pages/                  # Route pages
│   │   ├── store/                  # Zustand stores
│   │   ├── types/                  # TypeScript types
│   │   └── locales/                # i18n translations (en, fa, ar, tr)
│   └── package.json
└── docs/
    ├── ARCHITECTURE_STANDARDS.md   # Mandatory architecture rules
    ├── REQUIREMENTS.md             # System requirements
    ├── IMPLEMENTATION_PLAN.md      # Development roadmap
    └── TESTING_SUMMARY.md          # Test coverage report
```

---

## 🗄️ Database Schema

### 7 Metadata Tables:

1. **`sync_batches`** - Tracks sync operations with metrics
2. **`failed_records`** - Dead-letter queue for failed records
3. **`pending_children`** - Parent-child resolution queue
4. **`erp_sync_state`** - Delta detection state (last sync)
5. **`background_sync_schedule`** - Background sync configuration
6. **`entity_config`** - Entity configurations (business keys, parent refs)
7. **`field_mappings`** - Field transformation rules

### Dynamic Entity Tables:

SyncFlow creates tables in ScheduleHub with `_bridge_*` columns:
- `_bridge_uid` - UUID v7 primary key
- `_bridge_created_at` - Creation timestamp
- `_bridge_updated_at` - Last update timestamp
- `_bridge_erp_key_hash` - Business key hash (xxHash128)
- `_bridge_erp_data_hash` - Data hash (BLAKE3)
- `_bridge_erp_rowversion` - Source system rowversion
- `_bridge_erp_ref_str` - Human-readable reference string

---

## 🔑 Key Features

### 1. Delta Strategies

- **Full Sync**: All records are INSERTs (no delta detection)
- **Rowversion**: Compare `erp_rowversion` with stored value
- **Hash**: Compare `erp_data_hash` with stored value

### 2. Identity Engine

- **BK_HASH** (Business Key Hash): xxHash128 of business keys
- **DATA_HASH** (Data Hash): BLAKE3 of all data fields
- **Rowversion**: Extracted if available from source
- **Reference String**: Human-readable debug string

### 3. Parent-Child Resolution

- Detects missing parent references from `entity_config.parent_refs_config`
- Queues children in `pending_children` table
- Retries with exponential backoff (max 5 attempts)
- Resolves automatically when parent arrives

### 4. Background Sync

- Enforces time window: 19:00-07:00
- Splits large datasets across `days_to_complete` (default 7 days)
- Tracks `current_offset` for resumability
- Uses APScheduler for job management

### 5. Error Handling

- Failed records logged in `failed_records` table
- Includes raw data, normalized data, error details, stack trace
- Retry count tracking with exponential backoff
- Manual retry via API: `POST /api/v1/sync/retry-failed`

---

## 📡 API Endpoints

### Base URL: `http://127.0.0.1:8008/api/v1`

### Sync Operations
- `POST /sync/start` - Start realtime sync
- `GET /sync/status/{batch_uid}` - Check batch status
- `POST /sync/stop/{batch_uid}` - Cancel running sync
- `GET /sync/history` - List sync batches
- `POST /sync/retry-failed` - Retry failed records

### Entity Configuration
- `GET /entities` - List configured entities
- `POST /entities` - Create entity configuration
- `GET /entities/{uid}` - Get entity details
- `PUT /entities/{uid}` - Update entity config
- `DELETE /entities/{uid}` - Delete entity

### Monitoring
- `GET /failed-records` - List failed records
- `GET /pending-children` - List pending children
- `GET /stats` - Sync statistics
- `GET /metrics` - Prometheus metrics
- `GET /health` - Health check

### Schedules
- `GET /schedules` - List background sync schedules
- `POST /schedules` - Create schedule
- `PUT /schedules/{uid}` - Update schedule
- `DELETE /schedules/{uid}` - Delete schedule

---

## 🧪 Testing

### Test Coverage: >80%

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_normalization.py

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration
```

### Test Statistics:
- ✅ **93+ unit tests** covering all core functionality
- ✅ **10+ integration tests** for end-to-end validation
- ✅ Normalization: 25+ tests
- ✅ Identity: 23+ tests
- ✅ Delta: 19+ tests
- ✅ Parent-Child: 16+ tests
- ✅ Integration: 10+ tests

See [TESTING_SUMMARY.md](TESTING_SUMMARY.md) for detailed test documentation.

---

## 🎨 Frontend Features

### Dashboard
- Real-time sync metrics
- System health monitoring
- Recent sync activity timeline
- Quick action buttons

### Entity Management
- Inline expandable forms (no drawers/modals)
- Business key configuration
- Parent reference setup
- Sync status indicators

### Sync Operations
- Start sync with entity selection
- View batch history
- Monitor progress in real-time
- Retry failed records

### Monitoring
- Failed records viewer with filters
- Pending children tracker
- Metrics charts (success rate, throughput)
- Export capabilities

### Settings
- Dark/Light mode toggle
- Language switcher (EN, FA, AR, TR)
- RTL support for Arabic/Persian
- API token management

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# Application
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8008
API_PREFIX=/api/v1

# Database (SyncFlow Metadata)
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=dev_db
POSTGRES_SCHEMA=dev_schema
POSTGRES_USER=dev_user
POSTGRES_PASSWORD=dev_password

# APISmith Service
APISmith_URL=http://127.0.0.1:8007
APISmith_TOKEN=your-service-token-here

# ScheduleHub Service
ScheduleHub_URL=http://127.0.0.1:5180
ScheduleHub_TOKEN=your-service-token-here

# Sync Configuration
DEFAULT_BATCH_SIZE=1000
MAX_BATCH_SIZE=10000
DEFAULT_SYNC_INTERVAL_SECONDS=300
SYNC_WORKER_THREADS=4

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY_SECONDS=60
MAX_RETRY_DELAY_SECONDS=3600

# Background Sync
BACKGROUND_SYNC_ENABLED=True
BACKGROUND_SYNC_WINDOW_START=19:00:00
BACKGROUND_SYNC_WINDOW_END=07:00:00

# Security
INTERNAL_SERVICE_JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📚 Documentation

- [ARCHITECTURE_STANDARDS.md](ARCHITECTURE_STANDARDS.md) - Mandatory coding standards
- [REQUIREMENTS.md](REQUIREMENTS.md) - System requirements and specifications
- [IMPLEMENTATION_PLAN.md](backend/docs/IMPLEMENTATION_PLAN.md) - Development roadmap
- [TESTING_SUMMARY.md](TESTING_SUMMARY.md) - Test coverage report

---

## 🔧 Development

### Backend Development

```bash
# Install dev dependencies
uv sync

# Run with hot reload
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8008

# Format code
uv run black app/
uv run isort app/

# Type checking
uv run mypy app/

# Lint
uv run ruff check app/
```

### Frontend Development

```bash
# Install dependencies
pnpm install

# Development server (port 3008)
pnpm run dev

# Build for production
pnpm run build

# Type checking
pnpm run type-check

# Lint
pnpm run lint
```

### Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1

# View history
uv run alembic history
```

---

## 🚀 Deployment

### Docker Deployment (Recommended)

```bash
# Build image
docker build -t syncflow:latest .

# Run container
docker run -d \
  --name syncflow \
  -p 8008:8008 \
  -e POSTGRES_HOST=db \
  -e POSTGRES_PASSWORD=secure_password \
  syncflow:latest
```

### Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/syncflow.service

# Enable and start
sudo systemctl enable syncflow
sudo systemctl start syncflow

# View logs
sudo journalctl -u syncflow -f
```

---

## 📊 Performance Targets

- ✅ **Process 1M rows in <10 seconds**
- ✅ **Delta detection accuracy: 100%**
- ✅ **Parent-child resolution: 100%**
- ✅ **Error rate: <0.2%**
- ✅ **Background sync: 7-day window for large datasets**

---

## 🤝 Integration with Other Services

### APISmith Integration
- Fetches connector metadata and API definitions
- Executes queries via runtime API
- Handles pagination and result sets
- JWT authentication with token refresh

### ScheduleHub Integration
- Creates dynamic entity tables with `_bridge_*` columns
- Performs bulk INSERT/UPDATE/DELETE operations
- Checks record existence for delta detection
- Handles FK resolution for parent-child dependencies

---

## 🛡️ Security

- JWT token-based authentication for inter-service communication
- Environment-based secrets management
- No passwords in code or logs
- SQL injection prevention (parameterized queries)
- Rate limiting for API endpoints
- CORS configuration for frontend access

---

## 📝 License

Proprietary - Mahur Mehdashti © 2025

---

## 👨‍💻 Author

**Mahur Mehdashti**
Email: mehdashti@gmail.com
Date: December 2025

---

## 🎯 Status Summary

| Component | Status | Coverage |
|-----------|--------|----------|
| Backend Core | ✅ Complete | ~95% |
| Backend Tests | ✅ Complete | >80% |
| Frontend | ✅ Complete | 100% |
| API Routes | ✅ Complete | 100% |
| Database Schema | ✅ Complete | 100% |
| Documentation | ✅ Complete | 100% |

**SyncFlow is production-ready!** 🚀
