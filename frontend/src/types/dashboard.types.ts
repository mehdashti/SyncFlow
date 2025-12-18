// Dashboard statistics types

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
