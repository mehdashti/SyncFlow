import { Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'
import { Home } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
  const { t } = useTranslation()

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <h1 className="text-6xl font-bold text-neutral-900 dark:text-neutral-100">404</h1>
      <p className="mt-4 text-xl text-neutral-600 dark:text-neutral-400">
        Page not found
      </p>
      <p className="mt-2 text-neutral-500">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link to="/">
        <Button className="mt-6">
          <Home className="me-2 h-4 w-4" />
          {t('nav.dashboard')}
        </Button>
      </Link>
    </div>
  )
}
