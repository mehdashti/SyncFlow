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

export interface RecentSyncRun {
  uid: string
  entity_name: string
  status: SyncStatus
  started_at_utc: string
  records_fetched: number
}
