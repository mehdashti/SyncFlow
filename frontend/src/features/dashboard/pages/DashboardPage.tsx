import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Plug, Database, RefreshCw, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { dashboardService, syncService } from '@/api/services'
import { formatRelativeTime } from '@/lib/utils'
import type { SyncStatus } from '@/types'

function StatCard({
  title,
  value,
  icon: Icon,
  description,
}: {
  title: string
  value: number | string
  icon: React.ElementType
  description?: string
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </CardContent>
    </Card>
  )
}

function getStatusBadge(status: SyncStatus) {
  switch (status) {
    case 'success':
      return <Badge variant="success">Success</Badge>
    case 'failed':
      return <Badge variant="destructive">Failed</Badge>
    case 'running':
      return <Badge variant="warning">Running</Badge>
  }
}

export function DashboardPage() {
  const { t } = useTranslation()

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardService.getStats,
  })

  const { data: recentSyncs = [] } = useQuery({
    queryKey: ['recent-syncs'],
    queryFn: () => syncService.getRecent(10),
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('dashboard.title')}</h1>
        <p className="text-muted-foreground">{t('dashboard.welcome')}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title={t('dashboard.totalConnectors')}
          value={stats?.total_connectors ?? 0}
          icon={Plug}
          description={`${stats?.active_connectors ?? 0} ${t('dashboard.active')}`}
        />
        <StatCard
          title={t('dashboard.totalEntities')}
          value={stats?.total_entities ?? 0}
          icon={Database}
          description={`${stats?.enabled_entities ?? 0} ${t('dashboard.enabled')}`}
        />
        <StatCard
          title={t('dashboard.syncsToday')}
          value={stats?.total_sync_runs_today ?? 0}
          icon={RefreshCw}
          description={`${stats?.successful_syncs_today ?? 0} ${t('dashboard.successful')}`}
        />
        <StatCard
          title={t('dashboard.failedToday')}
          value={stats?.failed_syncs_today ?? 0}
          icon={AlertCircle}
        />
      </div>

      {/* Recent Syncs */}
      <Card>
        <CardHeader>
          <CardTitle>{t('dashboard.recentSyncs')}</CardTitle>
        </CardHeader>
        <CardContent>
          {recentSyncs.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">{t('common.noData')}</p>
          ) : (
            <div className="space-y-4">
              {recentSyncs.map((sync) => (
                <div
                  key={sync.uid}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {sync.status === 'success' && (
                      <CheckCircle className="h-5 w-5 text-success" />
                    )}
                    {sync.status === 'failed' && (
                      <AlertCircle className="h-5 w-5 text-destructive" />
                    )}
                    {sync.status === 'running' && (
                      <Clock className="h-5 w-5 text-warning animate-pulse" />
                    )}
                    <div>
                      <p className="font-medium">{sync.entity_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatRelativeTime(sync.started_at_utc)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground">
                      {sync.records_fetched} {t('dashboard.records')}
                    </span>
                    {getStatusBadge(sync.status)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
