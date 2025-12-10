import { apiClient } from '../client'
import type { FailedRecord, PendingChild, PaginatedResponse } from '../types'

export const monitoringService = {
  // Failed Records
  getFailedRecords: (params?: { page?: number; page_size?: number; entity_name?: string; is_resolved?: boolean }) =>
    apiClient.get<PaginatedResponse<FailedRecord>>('/failed-records', { params }),

  getFailedRecord: (uid: string) =>
    apiClient.get<FailedRecord>(`/failed-records/${uid}`),

  retryFailedRecord: (uid: string) =>
    apiClient.post(`/failed-records/${uid}/retry`),

  resolveFailedRecord: (uid: string) =>
    apiClient.post(`/failed-records/${uid}/resolve`),

  // Pending Children
  getPendingChildren: (params?: { page?: number; page_size?: number; child_entity?: string; parent_entity?: string }) =>
    apiClient.get<PaginatedResponse<PendingChild>>('/pending-children', { params }),

  getPendingChild: (uid: string) =>
    apiClient.get<PendingChild>(`/pending-children/${uid}`),
}
