// Common types used across the application

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export type UserRole = 'admin' | 'user' | 'viewer'

export interface UserProfile {
  uid: string
  email: string
  full_name: string
  roles: UserRole[]
  locale: string
  theme: 'light' | 'dark'
  is_active: boolean
  created_at_utc: string
}
