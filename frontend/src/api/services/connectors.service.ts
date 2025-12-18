import { API_ENDPOINTS } from '../endpoints'
import { apiClient } from '../client'
import type {
  Connector,
  ConnectorCreate,
  ConnectorUpdate,
  TestConnectionResult,
  DiscoveryResult,
  PaginatedResponse,
} from '@/types'

export const connectorsService = {
  getAll: async (): Promise<Connector[]> => {
    const response = await apiClient.get<PaginatedResponse<Connector> | Connector[]>(API_ENDPOINTS.CONNECTORS.LIST)
    // Handle both paginated and array responses
    if (Array.isArray(response.data)) {
      return response.data
    }
    return response.data.items
  },

  getById: async (uid: string): Promise<Connector> => {
    const response = await apiClient.get<Connector>(`/connectors/${uid}`)
    return response.data
  },

  create: async (data: ConnectorCreate): Promise<Connector> => {
    const response = await apiClient.post<Connector>(API_ENDPOINTS.CONNECTORS.LIST, data)
    return response.data
  },

  update: async (uid: string, data: ConnectorUpdate): Promise<Connector> => {
    const response = await apiClient.put<Connector>(`/connectors/${uid}`, data)
    return response.data
  },

  delete: async (uid: string): Promise<void> => {
    await apiClient.delete(`/connectors/${uid}`)
  },

  test: async (uid: string): Promise<TestConnectionResult> => {
    const response = await apiClient.post<TestConnectionResult>(`/connectors/${uid}/test`)
    return response.data
  },

  discover: async (uid: string): Promise<DiscoveryResult> => {
    const response = await apiClient.post<DiscoveryResult>(`/connectors/${uid}/discover`)
    return response.data
  },
}
