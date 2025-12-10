// Common Types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Entity Types
export interface Entity {
  uid: string
  entity_name: string
  source_system: string
  business_key_fields: string[]
  parent_refs: ParentRef[]
  sync_enabled: boolean
  created_at: string
  updated_at: string
}

export interface ParentRef {
  parent_entity: string
  ref_field: string
  parent_field: string
}

export interface CreateEntityRequest {
  entity_name: string
  source_system: string
  business_key_fields: string[]
  parent_refs?: ParentRef[]
  sync_enabled?: boolean
}

export interface UpdateEntityRequest extends Partial<CreateEntityRequest> {}

// Sync Types
export interface SyncStartRequest {
  entity_name: string
  sync_type: 'full' | 'incremental'
  connector_slug?: string
  business_keys?: string[]
}

export interface SyncProgress {
  fetched: number
  normalized: number
  mapped: number
  resolved: number
  merged: number
  inserted: number
  updated: number
  failed: number
}

export interface SyncStatusResponse {
  batch_uid: string
  entity_name: string
  sync_type: 'full' | 'incremental'
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: SyncProgress
  started_at: string
  completed_at?: string
  error_message?: string
}

export interface BatchHistory {
  items: SyncStatusResponse[]
  total: number
  page: number
  page_size: number
}

// Schedule Types
export interface Schedule {
  uid: string
  entity_name: string
  source_system: string
  time_window_start: string // "HH:MM:SS"
  time_window_end: string // "HH:MM:SS"
  days_to_complete: number
  rows_per_day?: number
  total_rows_estimate?: number
  current_progress: number
  total_progress_required: number
  is_enabled: boolean
  last_run_at?: string
  next_run_at?: string
  created_at: string
  updated_at: string
}

export interface CreateScheduleRequest {
  entity_name: string
  source_system: string
  time_window_start: string
  time_window_end: string
  days_to_complete: number
  rows_per_day?: number
  total_rows_estimate?: number
  is_enabled?: boolean
}

export interface UpdateScheduleRequest extends Partial<CreateScheduleRequest> {}

export interface SchedulerStatus {
  is_running: boolean
  active_jobs: number
  next_run?: string
}

// Mapping Types
export interface FieldMapping {
  uid: string
  entity_name: string
  source_field: string
  target_field: string
  transformation?: string
  default_value?: string
  is_required: boolean
  created_at: string
  updated_at: string
}

export interface CreateMappingRequest {
  entity_name: string
  source_field: string
  target_field: string
  transformation?: string
  default_value?: string
  is_required?: boolean
}

// Monitoring Types
export interface FailedRecord {
  uid: string
  batch_uid: string
  entity_name: string
  stage_failed: string
  error_type: string
  error_message: string
  retry_count: number
  max_retries: number
  raw_data?: Record<string, unknown>
  normalized_data?: Record<string, unknown>
  is_resolved: boolean
  created_at: string
  resolved_at?: string
}

export interface PendingChild {
  uid: string
  child_entity: string
  parent_entity: string
  parent_business_key: string
  missing_parent_field: string
  child_data: Record<string, unknown>
  created_at: string
}

// Stats Types
export interface DashboardStats {
  active_syncs: number
  today_batches: number
  failed_records: number
  pending_children: number
  success_rate: number
  last_sync?: SyncStatusResponse
}

// Health Types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  database: 'healthy' | 'unhealthy'
  connector: 'healthy' | 'unhealthy'
  smartplan: 'healthy' | 'unhealthy'
}
