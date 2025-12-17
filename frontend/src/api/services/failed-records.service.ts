import { apiClient } from '../client'
import type { FailedRecord, PaginatedResponse } from '@/types'

export const failedRecordsService = {
  getAll: async (): Promise<FailedRecord[]> => {
    const response = await apiClient.get<PaginatedResponse<FailedRecord> | FailedRecord[]>(
      '/failed-records'
    )
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  getById: async (uid: string): Promise<FailedRecord> => {
    const response = await apiClient.get<FailedRecord>(`/failed-records/${uid}`)
    return response.data
  },

  getByEntity: async (entityUid: string): Promise<FailedRecord[]> => {
    const response = await apiClient.get<PaginatedResponse<FailedRecord> | FailedRecord[]>(
      `/entities/${entityUid}/failed-records`
    )
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  retry: async (uid: string): Promise<void> => {
    await apiClient.post(`/failed-records/${uid}/retry`)
  },

  retryAll: async (entityUid: string): Promise<{ retried_count: number }> => {
    const response = await apiClient.post<{ retried_count: number }>(
      `/entities/${entityUid}/failed-records/retry-all`
    )
    return response.data
  },

  resolve: async (uid: string): Promise<void> => {
    await apiClient.post(`/failed-records/${uid}/resolve`)
  },

  delete: async (uid: string): Promise<void> => {
    await apiClient.delete(`/failed-records/${uid}`)
  },
}
