import { useTranslation } from 'react-i18next'
import { Sun, Moon, Monitor, Globe, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useUIStore } from '@/store'
import { languages } from '@/i18n'
import { cn } from '@/lib/cn'

export function Header() {
  const { t } = useTranslation()
  const { theme, setTheme, locale, setLocale, sidebarCollapsed } = useUIStore()

  const themeOptions = [
    { value: 'light' as const, icon: Sun, label: t('settings.themeLight') },
    { value: 'dark' as const, icon: Moon, label: t('settings.themeDark') },
    { value: 'system' as const, icon: Monitor, label: t('settings.themeSystem') },
  ]

  const currentTheme = themeOptions.find((opt) => opt.value === theme)

  return (
    <header
      className={cn(
        'fixed top-0 z-30 flex h-14 items-center justify-between border-b border-neutral-200 bg-white px-4 transition-all duration-300 dark:border-neutral-700 dark:bg-neutral-900',
        sidebarCollapsed ? 'start-16' : 'start-60',
        'end-0'
      )}
    >
      {/* Left side - Page title / Breadcrumb area */}
      <div className="flex items-center gap-4">
        {/* Placeholder for breadcrumbs or page title */}
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center gap-2">
        {/* Refresh Button */}
        <Button variant="ghost" size="icon" className="h-9 w-9">
          <RefreshCw className="h-4 w-4" />
        </Button>

        {/* Theme Switcher */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-9 w-9">
              {currentTheme && <currentTheme.icon className="h-4 w-4" />}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>{t('settings.theme')}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {themeOptions.map((option) => (
              <DropdownMenuItem
                key={option.value}
                onClick={() => setTheme(option.value)}
                className={cn(theme === option.value && 'bg-neutral-100 dark:bg-neutral-800')}
              >
                <option.icon className="me-2 h-4 w-4" />
                {option.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Language Switcher */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-9 w-9">
              <Globe className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>{t('settings.language')}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {languages.map((lang) => (
              <DropdownMenuItem
                key={lang.code}
                onClick={() => setLocale(lang.code as 'en' | 'fa' | 'ar' | 'tr')}
                className={cn(locale === lang.code && 'bg-neutral-100 dark:bg-neutral-800')}
              >
                {lang.name}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
