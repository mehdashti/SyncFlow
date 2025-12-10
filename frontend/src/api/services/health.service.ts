import { apiClient } from '../client'
import type { DashboardStats, HealthStatus } from '../types'

export const healthService = {
  getHealth: () =>
    apiClient.get<HealthStatus>('/health'),

  getStats: () =>
    apiClient.get<DashboardStats>('/stats'),
}
