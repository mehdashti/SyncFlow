import { apiClient } from '../client'
import type { FieldMapping, CreateMappingRequest, PaginatedResponse } from '../types'

export const mappingsService = {
  getAll: (params?: { page?: number; page_size?: number; entity_name?: string }) =>
    apiClient.get<PaginatedResponse<FieldMapping>>('/mappings', { params }),

  getByUid: (uid: string) =>
    apiClient.get<FieldMapping>(`/mappings/${uid}`),

  create: (data: CreateMappingRequest) =>
    apiClient.post<FieldMapping>('/mappings', data),

  update: (uid: string, data: Partial<CreateMappingRequest>) =>
    apiClient.put<FieldMapping>(`/mappings/${uid}`, data),

  delete: (uid: string) =>
    apiClient.delete(`/mappings/${uid}`),
}
