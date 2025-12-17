import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw, Search, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { syncService, entitiesService } from '@/api/services'
import type { SyncRun, SyncStatus } from '@/types'
import { formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

export function SyncPage() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')

  const { data: syncRuns = [], isLoading, refetch } = useQuery({
    queryKey: ['sync-runs'],
    queryFn: syncService.getAll,
    refetchInterval: 5000, // Poll every 5 seconds for running syncs
  })

  const { data: entities = [] } = useQuery({
    queryKey: ['entities'],
    queryFn: entitiesService.getAll,
  })

  const filteredRuns = syncRuns.filter((run) => {
    const entity = entities.find((e) => e.uid === run.entity_uid)
    return entity?.api_name.toLowerCase().includes(search.toLowerCase()) ||
      run.entity_name?.toLowerCase().includes(search.toLowerCase())
  })

  const getEntityName = (run: SyncRun) => {
    if (run.entity_name) return run.entity_name
    const entity = entities.find((e) => e.uid === run.entity_uid)
    return entity?.api_name || run.entity_uid
  }

  const getStatusIcon = (status: SyncStatus) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return null
    }
  }

  const getStatusBadge = (status: SyncStatus) => {
    const variants: Record<SyncStatus, 'default' | 'success' | 'destructive'> = {
      running: 'default',
      success: 'success',
      failed: 'destructive',
    }
    const labels: Record<SyncStatus, string> = {
      running: 'sync.status.running',
      success: 'sync.status.completed',
      failed: 'sync.status.failed',
    }
    return (
      <Badge variant={variants[status]}>
        {t(labels[status])}
      </Badge>
    )
  }

  const formatDuration = (startedAt: string, completedAt?: string | null) => {
    const start = new Date(startedAt).getTime()
    const end = completedAt ? new Date(completedAt).getTime() : Date.now()
    const duration = Math.round((end - start) / 1000)

    if (duration < 60) return `${duration}s`
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`
  }

  const totalRecords = (run: SyncRun) => {
    return run.records_fetched || 0
  }

  const syncedRecords = (run: SyncRun) => {
    return (run.records_inserted || 0) + (run.records_updated || 0)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('sync.title')}</h1>
          <p className="text-muted-foreground">{t('sync.description')}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t('common.search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button variant="outline" size="icon" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('sync.stats.total')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{syncRuns.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('sync.stats.running')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">
              {syncRuns.filter((r) => r.status === 'running').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('sync.stats.completed')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {syncRuns.filter((r) => r.status === 'success').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('sync.stats.failed')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {syncRuns.filter((r) => r.status === 'failed').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sync Runs List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="py-4">
                <div className="h-4 w-1/3 bg-muted rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredRuns.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <RefreshCw className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{t('sync.noRuns')}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredRuns.map((run) => (
            <Card
              key={run.uid}
              className={cn(
                'transition-all',
                run.status === 'running' && 'border-blue-500/50'
              )}
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {getStatusIcon(run.status)}
                    <div>
                      <p className="font-medium">{getEntityName(run)}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatRelativeTime(run.started_at_utc)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right text-sm">
                      <p className="text-muted-foreground">{t('sync.records')}</p>
                      <p className="font-medium">
                        {syncedRecords(run)} / {totalRecords(run)}
                      </p>
                    </div>
                    <div className="text-right text-sm">
                      <p className="text-muted-foreground">{t('sync.duration')}</p>
                      <p className="font-medium">
                        {formatDuration(run.started_at_utc, run.completed_at_utc)}
                      </p>
                    </div>
                    {getStatusBadge(run.status)}
                  </div>
                </div>
                {run.error_message && (
                  <div className="mt-3 p-2 bg-destructive/10 text-destructive text-sm rounded">
                    {run.error_message}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
