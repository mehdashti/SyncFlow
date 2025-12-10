import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'

interface InlineConfirmProps {
  trigger: React.ReactNode
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: 'destructive' | 'warning' | 'default'
  onConfirm: () => void | Promise<void>
}

export function InlineConfirm({
  trigger,
  title,
  description,
  confirmText,
  cancelText,
  variant = 'default',
  onConfirm,
}: InlineConfirmProps) {
  const { t } = useTranslation()
  const [isConfirming, setIsConfirming] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleConfirm = async () => {
    setIsLoading(true)
    try {
      await onConfirm()
    } finally {
      setIsLoading(false)
      setIsConfirming(false)
    }
  }

  if (!isConfirming) {
    return <span onClick={() => setIsConfirming(true)}>{trigger}</span>
  }

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-md border p-2',
        variant === 'destructive' && 'border-error-200 bg-error-50 dark:border-error-800 dark:bg-error-900/20',
        variant === 'warning' && 'border-warning-200 bg-warning-50 dark:border-warning-800 dark:bg-warning-900/20',
        variant === 'default' && 'border-neutral-200 bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-800'
      )}
    >
      <div className="text-sm">
        <p className="font-medium text-neutral-900 dark:text-neutral-100">{title}</p>
        {description && (
          <p className="text-neutral-500 dark:text-neutral-400">{description}</p>
        )}
      </div>
      <div className="flex gap-1">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setIsConfirming(false)}
          disabled={isLoading}
        >
          {cancelText || t('common.cancel')}
        </Button>
        <Button
          size="sm"
          variant={variant === 'destructive' ? 'destructive' : 'default'}
          onClick={handleConfirm}
          disabled={isLoading}
        >
          {confirmText || t('common.confirm')}
        </Button>
      </div>
    </div>
  )
}
