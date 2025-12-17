import { Link, useRouterState } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  Plug,
  Database,
  RefreshCw,
  Calendar,
  AlertCircle,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

const menuItems = [
  { path: '/', icon: LayoutDashboard, labelKey: 'sidebar.dashboard' },
  { path: '/connectors', icon: Plug, labelKey: 'sidebar.connectors' },
  { path: '/entities', icon: Database, labelKey: 'sidebar.entities' },
  { path: '/sync', icon: RefreshCw, labelKey: 'sidebar.sync' },
  { path: '/schedules', icon: Calendar, labelKey: 'sidebar.schedules' },
  { path: '/failed-records', icon: AlertCircle, labelKey: 'sidebar.failedRecords' },
  { path: '/settings', icon: Settings, labelKey: 'sidebar.settings' },
]

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { t } = useTranslation()
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  return (
    <aside
      className={cn(
        'fixed top-[var(--header-height)] left-0 h-[calc(100vh-var(--header-height))] bg-card border-r border-border transition-all duration-300 z-40',
        collapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-width)]'
      )}
    >
      <nav className="flex flex-col h-full p-2">
        <div className="flex-1 space-y-1">
          {menuItems.map((item) => {
            const isActive = currentPath === item.path
            const Icon = item.icon

            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
                title={collapsed ? t(item.labelKey) : undefined}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span>{t(item.labelKey)}</span>}
              </Link>
            )
          })}
        </div>

        <Button
          variant="ghost"
          size="sm"
          className="mt-auto"
          onClick={onToggle}
          title={collapsed ? t('sidebar.expand') : t('sidebar.collapse')}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span>{t('sidebar.collapse')}</span>
            </>
          )}
        </Button>
      </nav>
    </aside>
  )
}
