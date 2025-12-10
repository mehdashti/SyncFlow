# SyncFlow - API Summary

## Date: 2025-12-08

This document describes every SyncFlow API endpoint so the integration surface is fully documented for developers and automation.

---

## 🎯 API Overview

**Base URL**: `http://localhost:8008`
**API Prefix**: `/api/v1`
**Swagger UI**: `http://localhost:8008/api/v1/docs`
**ReDoc**: `http://localhost:8008/api/v1/redoc`

**Total Endpoints**: 13 (3 meta, 5 sync, 5 monitoring)

---

## 📋 Meta Endpoints

### 1. Root
```
GET /
```
**Description**: Service information summary
**Response**: metadata JSON with `service`, `version`, `status`, `docs`

### 2. Health Check
```
GET /api/v1/health
```
**Description**: Basic health probe for readiness/liveness
**Response**: `status`, `service`, `version`, `environment`

### 3. Metadata
```
GET /api/v1/metadata
```
**Description**: Detailed configuration, database, and downstream service URLs
**Response**: includes `app`, `version`, `environment`, `database` info, and `connector` and `smartplan` service URLs

---

## 🔄 Sync API Endpoints

### 1. Start Sync
```
POST /api/v1/sync/start
```
**Description**: Start a sync for a specific entity
**Request Body**: entity details, connector slug, business key fields, sync type, pagination controls
**Response**: 202 Accepted with batch UID, entity name, sync type, message, and start timestamp
**Features**: background execution, immediate response, batch creation, full/incremental modes

### 2. Get Sync Status
```
GET /api/v1/sync/status/{batch_uid}
```
**Description**: Fetch the latest status of a sync batch
**Path Parameter**: `batch_uid` (required)
**Response**: batch and record counts, status timestamps, error message
**Status values**: `pending`, `running`, `completed`, `failed`, `cancelled`

### 3. Stop Sync
```
POST /api/v1/sync/stop/{batch_uid}
```
**Description**: Stop a running sync batch
**Path Parameter**: `batch_uid`
**Response**: success flag and message
**Errors**: 404 when batch missing, 400 when not running

### 4. Get Sync History
```
GET /api/v1/sync/history?entity_name=&status=&page=1&page_size=50
```
**Description**: List sync batches with pagination
**Query parameters**: `entity_name` filter, `status`, `page`, `page_size` (default 50, max 100)
**Response**: paginated list of batches with counts and timestamps

### 5. Retry Failed Records
```
POST /api/v1/sync/retry-failed
```
**Description**: Retry the failed records from batches
**Request Body**: optional batch UID, entity name, `max_retries`, `limit`
**Response**: summary of retried, resolved, and still-failed records

---

## 📊 Monitoring API Endpoints

### 1. Get System Statistics
```
GET /api/v1/monitoring/stats
```
**Description**: Aggregated system statistics for dashboards
**Response**: counts of batches, failed records breakdown, pending children summaries, and generation timestamp

### 2. Get Failed Records
```
GET /api/v1/monitoring/failed-records?batch_uid=&entity_name=&error_type=&stage=&page=1&page_size=50
```
**Description**: Retrieve paginated failed records across entities
**Query parameters**: `batch_uid`, `entity_name`, `error_type`, `stage`, `page`, `page_size`
**Response**: list of failed record payloads, error info, retry counts

### 3. Get Pending Children
```
GET /api/v1/monitoring/pending-children?parent_entity=&entity_name=&page=1&page_size=50
```
**Description**: List child records waiting for parent sync
**Query parameters**: `parent_entity`, `entity_name`, `page`, `page_size`
**Response**: pending-child entries with parent references and retry metadata

### 4. Detailed Health Check
```
GET /api/v1/monitoring/health/detailed
```
**Description**: Health check with component breakdown
**Response**: statuses for database, connector API, ScheduleHub API with messages
**Status codes**: 200 Healthy, 503 Unhealthy

### 5. Prometheus Metrics
```
GET /api/v1/monitoring/metrics/prometheus
```
**Description**: Expose Prometheus-formatted metrics
**Response**: textual metrics for batches, statuses, failed records, and retryable counts

---

## 🔐 Authentication

**Current State**: No authentication in development
**Plan**: JWT token authentication for production deployments

---

## 📝 Error Responses

All endpoints follow standard FastAPI `HTTPException` formats:

```json
{
  "detail": "Error message here"
}
```

**Common status codes**: `200` (Success), `202` (Accepted), `400` (Bad Request), `404` (Not Found), `500` (Internal Server Error), `503` (Service Unavailable)

---

## 🚀 Usage Examples

### Example 1: Start Sync
```bash
curl -X POST http://localhost:8008/api/v1/sync/start \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "inventory_items",
    "connector_api_slug": "inventory_items",
    "business_key_fields": ["item_number"],
    "sync_type": "incremental",
    "page_size": 1000
  }'
```

### Example 2: Check Status
```bash
curl http://localhost:8008/api/v1/sync/status/01234567-89ab-cdef-0123-456789abcdef
```

### Example 3: Fetch Monitoring Stats
```bash
curl http://localhost:8008/api/v1/monitoring/stats
```

---

## 🧰 Notes

- All endpoints are asynchronous-friendly and support pagination where applicable.
- Monitoring endpoints provide enough context for dashboards and alerts.
- The retry API helps keep ingestions resilient when downstream data quality issues occur.
