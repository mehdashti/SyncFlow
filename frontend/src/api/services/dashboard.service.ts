import { apiClient } from '../client'
import { API_ENDPOINTS } from '../endpoints'
import type { DashboardStats, RecentSyncRun } from '@/types'

export const dashboardService = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await apiClient.get<DashboardStats>(API_ENDPOINTS.DASHBOARD.STATS)
    return response.data
  },

  getRecentSyncs: async (limit: number = 10): Promise<RecentSyncRun[]> => {
    const response = await apiClient.get<RecentSyncRun[]>(`/dashboard/recent-syncs?limit=${limit}`)
    return response.data
  },
}
