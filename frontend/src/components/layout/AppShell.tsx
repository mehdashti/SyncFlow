import { Outlet } from '@tanstack/react-router'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useUIStore } from '@/store'
import { cn } from '@/lib/cn'

export function AppShell() {
  const { sidebarCollapsed } = useUIStore()

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <Sidebar />
      <Header />
      <main
        className={cn(
          'min-h-screen pt-14 transition-all duration-300',
          sidebarCollapsed ? 'ps-16' : 'ps-60'
        )}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
