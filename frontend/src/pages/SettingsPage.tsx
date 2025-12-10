import { useTranslation } from 'react-i18next'
import { Sun, Moon, Monitor } from 'lucide-react'
import { PageHeader } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/store'
import { languages } from '@/i18n'
import { cn } from '@/lib/cn'

export default function SettingsPage() {
  const { t } = useTranslation()
  const { theme, setTheme, locale, setLocale } = useUIStore()

  const themeOptions = [
    { value: 'light' as const, icon: Sun, label: t('settings.themeLight') },
    { value: 'dark' as const, icon: Moon, label: t('settings.themeDark') },
    { value: 'system' as const, icon: Monitor, label: t('settings.themeSystem') },
  ]

  return (
    <div>
      <PageHeader title={t('settings.title')} />

      <div className="space-y-6 max-w-2xl">
        {/* Theme Settings */}
        <Card>
          <CardHeader>
            <CardTitle>{t('settings.theme')}</CardTitle>
            <CardDescription>Choose your preferred theme</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {themeOptions.map((option) => (
                <Button
                  key={option.value}
                  variant={theme === option.value ? 'default' : 'outline'}
                  onClick={() => setTheme(option.value)}
                  className="flex-1"
                >
                  <option.icon className="me-2 h-4 w-4" />
                  {option.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Language Settings */}
        <Card>
          <CardHeader>
            <CardTitle>{t('settings.language')}</CardTitle>
            <CardDescription>Select your preferred language</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {languages.map((lang) => (
                <Button
                  key={lang.code}
                  variant={locale === lang.code ? 'default' : 'outline'}
                  onClick={() => setLocale(lang.code as 'en' | 'fa' | 'ar' | 'tr')}
                  className={cn('justify-start', lang.dir === 'rtl' && 'font-vazirmatn')}
                >
                  {lang.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* API Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>Backend API settings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  API Base URL
                </label>
                <p className="mt-1 font-mono text-sm text-neutral-500 bg-neutral-100 dark:bg-neutral-800 p-2 rounded">
                  {import.meta.env.VITE_API_URL || 'http://localhost:8008/api/v1'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
