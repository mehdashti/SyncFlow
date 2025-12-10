import { create } from 'zustand'

interface TableFilters {
  search: string
  entity?: string
  status?: string
  dateFrom?: string
  dateTo?: string
}

interface FilterState {
  // Sync History Filters
  syncFilters: TableFilters
  setSyncFilters: (filters: Partial<TableFilters>) => void
  resetSyncFilters: () => void

  // Failed Records Filters
  failedFilters: TableFilters & { isResolved?: boolean }
  setFailedFilters: (filters: Partial<TableFilters & { isResolved?: boolean }>) => void
  resetFailedFilters: () => void

  // Schedule Filters
  scheduleFilters: TableFilters & { isEnabled?: boolean }
  setScheduleFilters: (filters: Partial<TableFilters & { isEnabled?: boolean }>) => void
  resetScheduleFilters: () => void
}

const defaultFilters: TableFilters = {
  search: '',
  entity: undefined,
  status: undefined,
  dateFrom: undefined,
  dateTo: undefined,
}

export const useFilterStore = create<FilterState>((set) => ({
  // Sync History Filters
  syncFilters: { ...defaultFilters },
  setSyncFilters: (filters) =>
    set((state) => ({
      syncFilters: { ...state.syncFilters, ...filters },
    })),
  resetSyncFilters: () => set({ syncFilters: { ...defaultFilters } }),

  // Failed Records Filters
  failedFilters: { ...defaultFilters, isResolved: false },
  setFailedFilters: (filters) =>
    set((state) => ({
      failedFilters: { ...state.failedFilters, ...filters },
    })),
  resetFailedFilters: () => set({ failedFilters: { ...defaultFilters, isResolved: false } }),

  // Schedule Filters
  scheduleFilters: { ...defaultFilters, isEnabled: undefined },
  setScheduleFilters: (filters) =>
    set((state) => ({
      scheduleFilters: { ...state.scheduleFilters, ...filters },
    })),
  resetScheduleFilters: () => set({ scheduleFilters: { ...defaultFilters, isEnabled: undefined } }),
}))
