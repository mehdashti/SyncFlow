import { apiClient } from '../client'
import type { Entity, EntityUpdate, PaginatedResponse } from '@/types'

export const entitiesService = {
  getAll: async (): Promise<Entity[]> => {
    const response = await apiClient.get<PaginatedResponse<Entity> | Entity[]>('/entities')
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  getById: async (uid: string): Promise<Entity> => {
    const response = await apiClient.get<Entity>(`/entities/${uid}`)
    return response.data
  },

  getByConnector: async (connectorUid: string): Promise<Entity[]> => {
    const response = await apiClient.get<PaginatedResponse<Entity> | Entity[]>(
      `/connectors/${connectorUid}/entities`
    )
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  update: async (uid: string, data: EntityUpdate): Promise<Entity> => {
    const response = await apiClient.put<Entity>(`/entities/${uid}`, data)
    return response.data
  },

  delete: async (uid: string): Promise<void> => {
    await apiClient.delete(`/entities/${uid}`)
  },

  triggerSync: async (uid: string): Promise<{ sync_run_uid: string }> => {
    const response = await apiClient.post<{ sync_run_uid: string }>(`/entities/${uid}/sync`)
    return response.data
  },

  triggerFullRefresh: async (uid: string): Promise<{ sync_run_uid: string }> => {
    const response = await apiClient.post<{ sync_run_uid: string }>(`/entities/${uid}/full-refresh`)
    return response.data
  },
}
