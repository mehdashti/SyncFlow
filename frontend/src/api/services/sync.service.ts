import { apiClient } from '../client'
import type { SyncStartRequest, SyncStatusResponse, BatchHistory } from '../types'

export const syncService = {
  startSync: (data: SyncStartRequest) =>
    apiClient.post<SyncStatusResponse>('/sync/start', data),

  getStatus: (batchUid: string) =>
    apiClient.get<SyncStatusResponse>(`/sync/status/${batchUid}`),

  stopSync: (batchUid: string) =>
    apiClient.post(`/sync/stop/${batchUid}`),

  getHistory: (params?: { page?: number; page_size?: number; entity_name?: string }) =>
    apiClient.get<BatchHistory>('/sync/history', { params }),

  retryFailed: (data: { batch_uid?: string; entity_name?: string }) =>
    apiClient.post('/sync/retry-failed', data),
}
