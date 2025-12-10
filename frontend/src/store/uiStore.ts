import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'
type Locale = 'en' | 'fa' | 'ar' | 'tr'

interface UIState {
  // Sidebar
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void

  // Theme
  theme: Theme
  setTheme: (theme: Theme) => void

  // Locale
  locale: Locale
  setLocale: (locale: Locale) => void

  // Drawer
  activeDrawer: string | null
  drawerData: unknown
  openDrawer: (name: string, data?: unknown) => void
  closeDrawer: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Sidebar
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      // Theme
      theme: 'system',
      setTheme: (theme) => set({ theme }),

      // Locale
      locale: 'en',
      setLocale: (locale) => set({ locale }),

      // Drawer
      activeDrawer: null,
      drawerData: null,
      openDrawer: (name, data = null) => set({ activeDrawer: name, drawerData: data }),
      closeDrawer: () => set({ activeDrawer: null, drawerData: null }),
    }),
    {
      name: 'bridge-ui-storage',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        theme: state.theme,
        locale: state.locale,
      }),
    }
  )
)
