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
