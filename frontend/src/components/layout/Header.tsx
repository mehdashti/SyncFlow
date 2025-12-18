import { useTranslation } from 'react-i18next'
import { RefreshCw, Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from './ThemeToggle'
import { LanguageSwitcher } from './LanguageSwitcher'
import { GlobalSearch } from '@/components/shell/GlobalSearch'
import { NotificationBell } from '@/components/shell/NotificationBell'

interface HeaderProps {
  onMenuToggle?: () => void
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { t } = useTranslation()

  return (
    <header className="fixed top-0 left-0 right-0 h-[var(--header-height)] bg-card border-b border-border z-50">
      <div className="flex items-center justify-between h-full px-4">
        {/* Left Section: Menu Toggle, Logo, App Name */}
        <div className="flex items-center gap-3">
          {onMenuToggle && (
            <Button variant="ghost" size="icon" onClick={onMenuToggle} className="shrink-0">
              <Menu className="h-5 w-5" />
            </Button>
          )}
          <div className="h-8 w-8 rounded-[3px] bg-primary flex items-center justify-center">
            <RefreshCw className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold hidden sm:block">{t('app.name')}</span>
        </div>

        {/* Right Section: Search, Theme, Notifications, Language */}
        <div className="flex items-center gap-1">
          {/* Global Search */}
          <GlobalSearch />

          <ThemeToggle />

          {/* Notifications */}
          <NotificationBell />

          <LanguageSwitcher />
        </div>
      </div>
    </header>
  )
}
