import { apiClient } from '../client'
import type { Schedule, CreateScheduleRequest, UpdateScheduleRequest, SchedulerStatus, PaginatedResponse } from '../types'

export const schedulesService = {
  getAll: (params?: { page?: number; page_size?: number; is_enabled?: boolean }) =>
    apiClient.get<PaginatedResponse<Schedule>>('/schedules', { params }),

  getByUid: (uid: string) =>
    apiClient.get<Schedule>(`/schedules/${uid}`),

  create: (data: CreateScheduleRequest) =>
    apiClient.post<Schedule>('/schedules', data),

  update: (uid: string, data: UpdateScheduleRequest) =>
    apiClient.patch<Schedule>(`/schedules/${uid}`, data),

  delete: (uid: string) =>
    apiClient.delete(`/schedules/${uid}`),

  resetProgress: (uid: string) =>
    apiClient.post(`/schedules/${uid}/reset`),

  triggerNow: (uid: string) =>
    apiClient.post(`/schedules/${uid}/trigger`),

  getStatus: () =>
    apiClient.get<SchedulerStatus>('/schedules/status'),

  getStats: () =>
    apiClient.get('/schedules/stats'),
}
