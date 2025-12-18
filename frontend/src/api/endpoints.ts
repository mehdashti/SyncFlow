/**
 * API Endpoints Configuration
 *
 * Centralized endpoint definitions for all API calls.
 * Based on APISmith standards.
 */

export const API_ENDPOINTS = {
  // Connectors (APISmith instances)
  CONNECTORS: {
    LIST: '/connectors',
    DETAIL: (uid: string) => `/connectors/${uid}`,
    CREATE: '/connectors',
    UPDATE: (uid: string) => `/connectors/${uid}`,
    DELETE: (uid: string) => `/connectors/${uid}`,
    TEST: (uid: string) => `/connectors/${uid}/test`,
    DISCOVER: (uid: string) => `/connectors/${uid}/discover`,
    ENTITIES: (uid: string) => `/connectors/${uid}/entities`,
  },

  // Entities (Discovered APIs)
  ENTITIES: {
    LIST: '/entities',
    DETAIL: (uid: string) => `/entities/${uid}`,
    UPDATE: (uid: string) => `/entities/${uid}`,
    DELETE: (uid: string) => `/entities/${uid}`,
    TRIGGER_SYNC: (uid: string) => `/entities/${uid}/sync`,
    FULL_REFRESH: (uid: string) => `/entities/${uid}/full-refresh`,
    RUNS: (uid: string) => `/entities/${uid}/runs`,
    FAILED_RECORDS: (uid: string) => `/entities/${uid}/failed-records`,
    RETRY_ALL_FAILED: (uid: string) => `/entities/${uid}/failed-records/retry-all`,
  },

  // Sync Runs
  SYNC_RUNS: {
    LIST: '/sync-runs',
    DETAIL: (uid: string) => `/sync-runs/${uid}`,
  },

  // Schedules
  SCHEDULES: {
    LIST: '/schedules',
    DETAIL: (uid: string) => `/schedules/${uid}`,
    CREATE: '/schedules',
    UPDATE: (uid: string) => `/schedules/${uid}`,
    DELETE: (uid: string) => `/schedules/${uid}`,
    PAUSE: (uid: string) => `/schedules/${uid}/pause`,
    RESUME: (uid: string) => `/schedules/${uid}/resume`,
  },

  // Failed Records
  FAILED_RECORDS: {
    LIST: '/failed-records',
    DETAIL: (uid: string) => `/failed-records/${uid}`,
    RETRY: (uid: string) => `/failed-records/${uid}/retry`,
    RESOLVE: (uid: string) => `/failed-records/${uid}/resolve`,
    DELETE: (uid: string) => `/failed-records/${uid}`,
  },

  // Dashboard
  DASHBOARD: {
    STATS: '/dashboard/stats',
    RECENT_SYNCS: (limit: number = 10) => `/sync-runs?limit=${limit}&sort=-started_at_utc`,
    RUNNING_SYNCS: '/sync-runs?status=running',
  },
} as const
