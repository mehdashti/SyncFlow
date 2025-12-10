import { useTranslation } from 'react-i18next'
import { PageHeader } from '@/components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  RefreshCw,
  Layers,
  AlertTriangle,
  Hourglass,
  TrendingUp,
  Clock,
} from 'lucide-react'

// KPI Card Component
function KPICard({
  title,
  value,
  change,
  changeType,
  icon: Icon,
}: {
  title: string
  value: string | number
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: React.ElementType
}) {
  return (
    <Card>
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
                className={`mt-1 text-sm ${
                  changeType === 'positive'
                    ? 'text-success-600'
                    : changeType === 'negative'
                    ? 'text-error-600'
                    : 'text-neutral-500'
                }`}
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

export default function DashboardPage() {
  const { t } = useTranslation()

  // Mock data - will be replaced with real API data
  const kpiData = [
    {
      title: t('dashboard.activeSyncs'),
      value: 3,
      change: '↑ 2',
      changeType: 'positive' as const,
      icon: RefreshCw,
    },
    {
      title: t('dashboard.todayBatches'),
      value: 47,
      change: '↑ 15',
      changeType: 'positive' as const,
      icon: Layers,
    },
    {
      title: t('dashboard.failedRecords'),
      value: 12,
      change: '↓ 5',
      changeType: 'positive' as const,
      icon: AlertTriangle,
    },
    {
      title: t('dashboard.pendingChildren'),
      value: 8,
      change: '↑ 3',
      changeType: 'negative' as const,
      icon: Hourglass,
    },
    {
      title: t('dashboard.successRate'),
      value: '99.2%',
      change: '↑ 0.3%',
      changeType: 'positive' as const,
      icon: TrendingUp,
    },
    {
      title: t('dashboard.lastSync'),
      value: '10:30',
      icon: Clock,
    },
  ]

  const recentSyncs = [
    { entity: 'inventory', status: 'completed', records: 1234, duration: '2m 30s', time: '10:30' },
    { entity: 'customers', status: 'running', records: '567/800', duration: '-', time: '10:45' },
    { entity: 'work_orders', status: 'pending', records: '-', duration: '-', time: 'Scheduled' },
  ]

  return (
    <div>
      <PageHeader title={t('dashboard.title')} />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {kpiData.map((kpi) => (
          <KPICard key={kpi.title} {...kpi} />
        ))}
      </div>

      {/* Recent Activity */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.recentActivity')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentSyncs.map((sync, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between border-b border-neutral-100 pb-3 last:border-0 last:pb-0 dark:border-neutral-800"
                >
                  <div className="flex items-center gap-3">
                    <div className="font-medium text-neutral-900 dark:text-neutral-100">
                      {sync.entity}
                    </div>
                    <Badge
                      variant={
                        sync.status === 'completed'
                          ? 'success'
                          : sync.status === 'running'
                          ? 'info'
                          : 'secondary'
                      }
                    >
                      {t(`status.${sync.status}`)}
                    </Badge>
                  </div>
                  <div className="text-sm text-neutral-500 dark:text-neutral-400">
                    {sync.records} • {sync.time}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('dashboard.systemHealth')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">Database</span>
                  <Badge variant="success">{t('status.healthy')}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">APISmith</span>
                  <Badge variant="success">{t('status.healthy')}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">ScheduleHub</span>
                  <Badge variant="success">{t('status.healthy')}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('dashboard.schedulerStatus')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">Status</span>
                  <Badge variant="success">{t('status.running')}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">
                    {t('schedule.activeJobs')}
                  </span>
                  <span className="font-medium text-neutral-900 dark:text-neutral-100">5</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-neutral-600 dark:text-neutral-400">
                    {t('schedule.nextRun')}
                  </span>
                  <span className="font-medium text-neutral-900 dark:text-neutral-100">19:00</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
