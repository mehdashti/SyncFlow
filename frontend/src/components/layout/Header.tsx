import { useTranslation } from 'react-i18next'
import { RefreshCw } from 'lucide-react'
import { ThemeToggle } from './ThemeToggle'
import { LanguageSwitcher } from './LanguageSwitcher'

export function Header() {
  const { t } = useTranslation()

  return (
    <header className="fixed top-0 left-0 right-0 h-[var(--header-height)] bg-card border-b border-border z-50">
      <div className="flex items-center justify-between h-full px-4">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <RefreshCw className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold hidden sm:block">{t('app.name')}</span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
