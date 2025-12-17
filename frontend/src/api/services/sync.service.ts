import { apiClient } from '../client'
import type { SyncRun, PaginatedResponse } from '@/types'

export const syncService = {
  getAll: async (): Promise<SyncRun[]> => {
    const response = await apiClient.get<PaginatedResponse<SyncRun> | SyncRun[]>('/sync-runs')
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  getById: async (uid: string): Promise<SyncRun> => {
    const response = await apiClient.get<SyncRun>(`/sync-runs/${uid}`)
    return response.data
  },

  getByEntity: async (entityUid: string): Promise<SyncRun[]> => {
    const response = await apiClient.get<PaginatedResponse<SyncRun> | SyncRun[]>(
      `/entities/${entityUid}/runs`
    )
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  getRecent: async (limit: number = 10): Promise<SyncRun[]> => {
    const response = await apiClient.get<PaginatedResponse<SyncRun> | SyncRun[]>(
      `/sync-runs?limit=${limit}&sort=-started_at_utc`
    )
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  getRunning: async (): Promise<SyncRun[]> => {
    const response = await apiClient.get<PaginatedResponse<SyncRun> | SyncRun[]>(
      '/sync-runs?status=running'
    )
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },
}
