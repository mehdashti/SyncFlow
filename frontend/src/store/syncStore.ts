import { create } from 'zustand'
import type { SyncProgress } from '@/api/types'

interface ActiveSync {
  batchUid: string
  entityName: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: SyncProgress
  startedAt: string
}

interface SyncState {
  activeSyncs: ActiveSync[]
  addActiveSync: (sync: ActiveSync) => void
  updateSync: (batchUid: string, data: Partial<ActiveSync>) => void
  removeSync: (batchUid: string) => void
  clearCompletedSyncs: () => void
}

export const useSyncStore = create<SyncState>((set) => ({
  activeSyncs: [],

  addActiveSync: (sync) =>
    set((state) => ({
      activeSyncs: [...state.activeSyncs, sync],
    })),

  updateSync: (batchUid, data) =>
    set((state) => ({
      activeSyncs: state.activeSyncs.map((sync) =>
        sync.batchUid === batchUid ? { ...sync, ...data } : sync
      ),
    })),

  removeSync: (batchUid) =>
    set((state) => ({
      activeSyncs: state.activeSyncs.filter((sync) => sync.batchUid !== batchUid),
    })),

  clearCompletedSyncs: () =>
    set((state) => ({
      activeSyncs: state.activeSyncs.filter(
        (sync) => sync.status !== 'completed' && sync.status !== 'failed'
      ),
    })),
}))
