import { useEffect } from 'react'
import { useUIStore } from '@/store'

export function useTheme() {
  const { theme, setTheme } = useUIStore()

  useEffect(() => {
    const root = window.document.documentElement

    const applyTheme = (resolvedTheme: 'light' | 'dark') => {
      root.setAttribute('data-theme', resolvedTheme)
      root.classList.remove('light', 'dark')
      root.classList.add(resolvedTheme)
    }

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      applyTheme(systemTheme)

      // Listen for system theme changes
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = (e: MediaQueryListEvent) => {
        applyTheme(e.matches ? 'dark' : 'light')
      }
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    } else {
      applyTheme(theme)
    }
  }, [theme])

  return { theme, setTheme }
}

export function useResolvedTheme(): 'light' | 'dark' {
  const { theme } = useUIStore()

  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return theme
}
