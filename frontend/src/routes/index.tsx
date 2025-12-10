import {
  createRouter,
  createRoute,
  createRootRoute,
} from '@tanstack/react-router'
import { AppShell } from '@/components/layout'

// Lazy load pages
import DashboardPage from '@/pages/DashboardPage'
import SyncPage from '@/pages/SyncPage'
import EntitiesPage from '@/pages/EntitiesPage'
import SchedulesPage from '@/pages/SchedulesPage'
import MappingsPage from '@/pages/MappingsPage'
import FailedRecordsPage from '@/pages/FailedRecordsPage'
import PendingChildrenPage from '@/pages/PendingChildrenPage'
import SettingsPage from '@/pages/SettingsPage'
import NotFoundPage from '@/pages/NotFoundPage'

// Root layout with AppShell
const rootRoute = createRootRoute({
  component: AppShell,
})

// Dashboard
const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardPage,
})

// Sync
const syncRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/sync',
  component: SyncPage,
})

// Entities
const entitiesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/entities',
  component: EntitiesPage,
})

// Schedules
const schedulesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/schedules',
  component: SchedulesPage,
})

// Mappings
const mappingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/mappings',
  component: MappingsPage,
})

// Monitoring - Failed Records
const failedRecordsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/monitoring/failed',
  component: FailedRecordsPage,
})

// Monitoring - Pending Children
const pendingChildrenRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/monitoring/pending',
  component: PendingChildrenPage,
})

// Settings
const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
})

// 404 - Not Found
const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '*',
  component: NotFoundPage,
})

// Route tree
const routeTree = rootRoute.addChildren([
  dashboardRoute,
  syncRoute,
  entitiesRoute,
  schedulesRoute,
  mappingsRoute,
  failedRecordsRoute,
  pendingChildrenRoute,
  settingsRoute,
  notFoundRoute,
])

// Create router
export const router = createRouter({ routeTree })

// Register router for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
