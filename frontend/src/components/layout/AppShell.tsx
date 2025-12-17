import { useState } from 'react'
import { Outlet } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function AppShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />

      <main
        className={cn(
          'pt-[var(--header-height)] transition-all duration-300',
          sidebarCollapsed ? 'pl-[var(--sidebar-collapsed)]' : 'pl-[var(--sidebar-width)]'
        )}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
