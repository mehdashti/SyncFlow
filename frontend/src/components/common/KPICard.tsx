import { cn } from '@/lib/cn'
import { Card, CardContent } from '@/components/ui/card'

interface KPICardProps {
  title: string
  value: string | number
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: React.ElementType
  className?: string
}

export function KPICard({
  title,
  value,
  change,
  changeType,
  icon: Icon,
  className,
}: KPICardProps) {
  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
              {title}
            </p>
            <p className="mt-1 text-3xl font-semibold text-neutral-900 dark:text-neutral-100">
              {value}
            </p>
            {change && (
              <p
                className={cn(
                  'mt-1 text-sm',
                  changeType === 'positive' && 'text-success-600',
                  changeType === 'negative' && 'text-error-600',
                  changeType === 'neutral' && 'text-neutral-500'
                )}
              >
                {change}
              </p>
            )}
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400">
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
