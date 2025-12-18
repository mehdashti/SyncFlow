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

export interface TestConnectionResult {
  success: boolean
  latency_ms: number | null
  error_message: string | null
}

export interface DiscoveryResult {
  discovered_count: number
  new_entities: number
  updated_entities: number
  entities: import('./entity.types').Entity[]
}
