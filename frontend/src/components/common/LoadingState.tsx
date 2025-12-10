import { useTranslation } from 'react-i18next'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/cn'

interface LoadingStateProps {
  text?: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export function LoadingState({ text, className, size = 'md' }: LoadingStateProps) {
  const { t } = useTranslation()

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  }

  return (
    <div className={cn('flex flex-col items-center justify-center py-12', className)}>
      <Loader2 className={cn('animate-spin text-primary-500', sizeClasses[size])} />
      <p className="mt-3 text-sm text-neutral-500 dark:text-neutral-400">
        {text || t('common.loading')}
      </p>
    </div>
  )
}
