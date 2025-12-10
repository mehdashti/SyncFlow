import { apiClient } from '../client'
import type { Entity, CreateEntityRequest, UpdateEntityRequest, PaginatedResponse } from '../types'

export const entitiesService = {
  getAll: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<Entity>>('/entities', { params }),

  getByUid: (uid: string) =>
    apiClient.get<Entity>(`/entities/${uid}`),

  create: (data: CreateEntityRequest) =>
    apiClient.post<Entity>('/entities', data),

  update: (uid: string, data: UpdateEntityRequest) =>
    apiClient.put<Entity>(`/entities/${uid}`, data),

  delete: (uid: string) =>
    apiClient.delete(`/entities/${uid}`),
}
