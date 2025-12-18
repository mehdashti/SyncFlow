// Common types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Connector types (APISmith instances)
export interface Connector {
  uid: string
  name: string
  base_url: string
  is_active: boolean
  last_tested_at_utc: string | null
  last_test_success: boolean | null
  created_at_utc: string
  updated_at_utc: string
}

export interface ConnectorCreate {
  name: string
  base_url: string
  auth_token?: string
  is_active?: boolean
}

export interface ConnectorUpdate {
  name?: string
  base_url?: string
  auth_token?: string
  is_active?: boolean
}

// Entity types (discovered APIs from APISmith)
export interface EntityColumn {
  name: string
  data_type: string
  is_nullable: boolean
  is_business_key: boolean
  is_row_version: boolean
}

export interface Entity {
  uid: string
  connector_uid: string
  connector_name: string
  slug: string
  api_name: string
  description: string | null
  delta_strategy: 'full' | 'rowversion' | 'hash'
  business_keys: string[]
  target_schema: string
  target_table: string
  columns: EntityColumn[]
  sync_enabled: boolean
  sync_interval_seconds: number
  last_sync_at_utc: string | null
  last_sync_status: 'success' | 'failed' | 'running' | null
  last_rowversion: string | null
  created_at_utc: string
  updated_at_utc: string
}

export interface EntityUpdate {
  sync_enabled?: boolean
  sync_interval_seconds?: number
  target_schema?: string
  target_table?: string
}

// Sync run types
export type SyncStatus = 'running' | 'success' | 'failed'

export interface SyncRun {
  uid: string
  entity_uid: string
  entity_name: string
  started_at_utc: string
  completed_at_utc: string | null
  status: SyncStatus
  records_fetched: number
  records_inserted: number
  records_updated: number
  records_unchanged: number
  records_failed: number
  rowversion_start: string | null
  rowversion_end: string | null
  error_message: string | null
  created_at_utc: string
}

// Schedule types
export interface Schedule {
  uid: string
  entity_uid: string
  entity_name: string
  cron_expression: string
  is_active: boolean
  last_run_at_utc: string | null
  next_run_at_utc: string | null
  created_at_utc: string
  updated_at_utc: string
}

export interface ScheduleCreate {
  entity_uid: string
  cron_expression: string
  is_active?: boolean
}

export interface ScheduleUpdate {
  cron_expression?: string
  is_active?: boolean
}

// Failed record types
export interface FailedRecord {
  uid: string
  sync_run_uid: string
  entity_uid: string
  entity_name: string
  record_data: Record<string, unknown>
  business_key: Record<string, unknown>
  error_message: string
  retry_count: number
  resolved: boolean
  created_at_utc: string
}

// Dashboard stats
export interface DashboardStats {
  total_connectors: number
  active_connectors: number
  total_entities: number
  enabled_entities: number
  total_sync_runs_today: number
  successful_syncs_today: number
  failed_syncs_today: number
  total_records_synced_today: number
}

export interface RecentSyncRun {
  uid: string
  entity_name: string
  status: SyncStatus
  started_at_utc: string
  records_fetched: number
}

// Test connection result
export interface TestConnectionResult {
  success: boolean
  latency_ms: number | null
  error_message: string | null
}

// Discovery result
export interface DiscoveryResult {
  discovered_count: number
  new_entities: number
  updated_entities: number
  entities: Entity[]
}

// User types (for future auth)
export interface UserProfile {
  uid: string
  email: string
  full_name: string
  roles: UserRole[]
  locale: string
  theme: 'light' | 'dark'
  is_active: boolean
  created_at_utc: string
}

export type UserRole = 'admin' | 'user' | 'viewer'
