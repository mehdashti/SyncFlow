import { useTranslation } from 'react-i18next'
import { Badge } from '@/components/ui/badge'

type Status = 'pending' | 'running' | 'completed' | 'failed' | 'enabled' | 'disabled' | 'healthy' | 'unhealthy'

interface StatusBadgeProps {
  status: Status
  size?: 'sm' | 'md'
}

const statusVariantMap: Record<Status, 'secondary' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'secondary',
  running: 'info',
  completed: 'success',
  failed: 'error',
  enabled: 'success',
  disabled: 'secondary',
  healthy: 'success',
  unhealthy: 'error',
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const { t } = useTranslation()

  return (
    <Badge
      variant={statusVariantMap[status]}
      className={size === 'sm' ? 'text-xs px-2 py-0' : ''}
    >
      {t(`status.${status}`)}
    </Badge>
  )
}
