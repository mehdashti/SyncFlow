import { cn } from '@/lib/cn'

interface ProgressBarProps {
  value: number
  max?: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function ProgressBar({
  value,
  max = 100,
  showLabel = true,
  size = 'md',
  className,
}: ProgressBarProps) {
  const percentage = Math.min(Math.round((value / max) * 100), 100)

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={cn('flex-1 bg-neutral-200 rounded-full dark:bg-neutral-700', sizeClasses[size])}>
        <div
          className={cn('bg-primary-500 rounded-full transition-all duration-300', sizeClasses[size])}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-neutral-600 dark:text-neutral-400 min-w-[3rem] text-end">
          {percentage}%
        </span>
      )}
    </div>
  )
}
