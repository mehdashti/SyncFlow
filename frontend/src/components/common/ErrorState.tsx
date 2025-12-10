import { useTranslation } from 'react-i18next'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Button } from '@/components/ui/button'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({ title, message, onRetry, className }: ErrorStateProps) {
  const { t } = useTranslation()

  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error-100 dark:bg-error-900/20">
        <AlertCircle className="h-6 w-6 text-error-600 dark:text-error-400" />
      </div>
      <h3 className="mt-4 text-sm font-medium text-neutral-900 dark:text-neutral-100">
        {title || t('common.error')}
      </h3>
      {message && (
        <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400 max-w-md">
          {message}
        </p>
      )}
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-4">
          <RefreshCw className="me-2 h-4 w-4" />
          {t('common.retry')}
        </Button>
      )}
    </div>
  )
}
