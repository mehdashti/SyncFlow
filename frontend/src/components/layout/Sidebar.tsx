import { Link, useRouterState } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  RefreshCw,
  Database,
  Clock,
  GitBranch,
  AlertTriangle,
  Hourglass,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import { useUIStore } from '@/store'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { Separator } from '@/components/ui/separator'

interface NavItem {
  path: string
  icon: React.ElementType
  labelKey: string
  badge?: number
}

const mainNavItems: NavItem[] = [
  { path: '/', icon: LayoutDashboard, labelKey: 'nav.dashboard' },
  { path: '/sync', icon: RefreshCw, labelKey: 'nav.sync' },
  { path: '/entities', icon: Database, labelKey: 'nav.entities' },
  { path: '/schedules', icon: Clock, labelKey: 'nav.schedules' },
  { path: '/mappings', icon: GitBranch, labelKey: 'nav.mappings' },
]

const monitoringNavItems: NavItem[] = [
  { path: '/monitoring/failed', icon: AlertTriangle, labelKey: 'nav.failedRecords' },
  { path: '/monitoring/pending', icon: Hourglass, labelKey: 'nav.pendingChildren' },
]

const bottomNavItems: NavItem[] = [
  { path: '/settings', icon: Settings, labelKey: 'nav.settings' },
]

function NavLink({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const { t } = useTranslation()
  const routerState = useRouterState()
  const isActive = routerState.location.pathname === item.path

  const linkContent = (
    <Link
      to={item.path}
      className={cn(
        'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
        'hover:bg-neutral-100 dark:hover:bg-neutral-800',
        isActive
          ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400'
          : 'text-neutral-600 dark:text-neutral-400',
        collapsed && 'justify-center px-2'
      )}
    >
      <item.icon className="h-5 w-5 shrink-0" />
      {!collapsed && <span>{t(item.labelKey)}</span>}
      {!collapsed && item.badge !== undefined && item.badge > 0 && (
        <span className="ms-auto rounded-full bg-error-500 px-2 py-0.5 text-xs text-white">
          {item.badge}
        </span>
      )}
    </Link>
  )

  if (collapsed) {
    return (
      <Tooltip delayDuration={0}>
        <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
        <TooltipContent side="right" sideOffset={10}>
          {t(item.labelKey)}
        </TooltipContent>
      </Tooltip>
    )
  }

  return linkContent
}

export function Sidebar() {
  const { t } = useTranslation()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()

  return (
    <aside
      className={cn(
        'fixed start-0 top-0 z-40 flex h-screen flex-col border-e border-neutral-200 bg-white transition-all duration-300 dark:border-neutral-700 dark:bg-neutral-900',
        sidebarCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center justify-between border-b border-neutral-200 px-4 dark:border-neutral-700">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500 text-white font-bold">
              B
            </div>
            <span className="font-semibold text-neutral-900 dark:text-neutral-100">
              SyncFlow
            </span>
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className={cn('h-8 w-8', sidebarCollapsed && 'mx-auto')}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2">
        {/* Main Navigation */}
        <div className="space-y-1">
          {mainNavItems.map((item) => (
            <NavLink key={item.path} item={item} collapsed={sidebarCollapsed} />
          ))}
        </div>

        {/* Monitoring Section */}
        <div className="mt-4">
          {!sidebarCollapsed && (
            <div className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
              {t('nav.monitoring')}
            </div>
          )}
          {sidebarCollapsed && <Separator className="my-2" />}
          <div className="space-y-1">
            {monitoringNavItems.map((item) => (
              <NavLink key={item.path} item={item} collapsed={sidebarCollapsed} />
            ))}
          </div>
        </div>
      </nav>

      {/* Bottom Navigation */}
      <div className="border-t border-neutral-200 p-2 dark:border-neutral-700">
        {bottomNavItems.map((item) => (
          <NavLink key={item.path} item={item} collapsed={sidebarCollapsed} />
        ))}
      </div>
    </aside>
  )
}
