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
