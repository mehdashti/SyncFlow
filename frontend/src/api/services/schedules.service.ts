import { apiClient } from '../client'
import { API_ENDPOINTS } from '../endpoints'
import type { Schedule, ScheduleCreate, ScheduleUpdate, PaginatedResponse } from '@/types'

export const schedulesService = {
  getAll: async (): Promise<Schedule[]> => {
    const response = await apiClient.get<PaginatedResponse<Schedule> | Schedule[]>(API_ENDPOINTS.SCHEDULES.LIST)
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  getById: async (uid: string): Promise<Schedule> => {
    const response = await apiClient.get<Schedule>(`/schedules/${uid}`)
    return response.data
  },

  create: async (data: ScheduleCreate): Promise<Schedule> => {
    const response = await apiClient.post<Schedule>(API_ENDPOINTS.SCHEDULES.LIST, data)
    return response.data
  },

  update: async (uid: string, data: ScheduleUpdate): Promise<Schedule> => {
    const response = await apiClient.put<Schedule>(`/schedules/${uid}`, data)
    return response.data
  },

  delete: async (uid: string): Promise<void> => {
    await apiClient.delete(`/schedules/${uid}`)
  },

  pause: async (uid: string): Promise<Schedule> => {
    const response = await apiClient.post<Schedule>(`/schedules/${uid}/pause`)
    return response.data
  },

  resume: async (uid: string): Promise<Schedule> => {
    const response = await apiClient.post<Schedule>(`/schedules/${uid}/resume`)
    return response.data
  },
}
