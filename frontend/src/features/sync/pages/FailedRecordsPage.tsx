import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, Search, Trash2, RotateCcw, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { failedRecordsService, entitiesService } from '@/api/services'
import type { FailedRecord } from '@/types'
import { formatRelativeTime } from '@/lib/utils'

export function FailedRecordsPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')

  const { data: failedRecords = [], isLoading, refetch } = useQuery({
    queryKey: ['failed-records'],
    queryFn: failedRecordsService.getAll,
  })

  const { data: entities = [] } = useQuery({
    queryKey: ['entities'],
    queryFn: entitiesService.getAll,
  })

  const retryMutation = useMutation({
    mutationFn: failedRecordsService.retry,
    onSuccess: () => {
      toast.success(t('failedRecords.retrySuccess'))
      queryClient.invalidateQueries({ queryKey: ['failed-records'] })
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: failedRecordsService.delete,
    onSuccess: () => {
      toast.success(t('success.deleted'))
      queryClient.invalidateQueries({ queryKey: ['failed-records'] })
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const filteredRecords = failedRecords.filter((record) => {
    const entity = entities.find((e) => e.uid === record.entity_uid)
    return (
      entity?.api_name.toLowerCase().includes(search.toLowerCase()) ||
      record.entity_name?.toLowerCase().includes(search.toLowerCase()) ||
      record.error_message.toLowerCase().includes(search.toLowerCase())
    )
  })

  const getEntityName = (record: FailedRecord) => {
    if (record.entity_name) return record.entity_name
    const entity = entities.find((e) => e.uid === record.entity_uid)
    return entity?.api_name || record.entity_uid
  }

  const handleDelete = (record: FailedRecord) => {
    if (window.confirm(t('failedRecords.deleteConfirm'))) {
      deleteMutation.mutate(record.uid)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('failedRecords.title')}</h1>
          <p className="text-muted-foreground">{t('failedRecords.description')}</p>
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

      {/* Stats Card */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {t('failedRecords.totalFailed')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-destructive">{failedRecords.length}</div>
        </CardContent>
      </Card>

      {/* Failed Records List */}
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
      ) : filteredRecords.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{t('failedRecords.noRecords')}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredRecords.map((record) => (
            <Card key={record.uid}>
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">{getEntityName(record)}</Badge>
                      <span className="text-sm text-muted-foreground">
                        {formatRelativeTime(record.created_at_utc)}
                      </span>
                      <Badge variant="secondary">
                        {t('failedRecords.retryCount')}: {record.retry_count}
                      </Badge>
                      {record.resolved && (
                        <Badge variant="success">{t('failedRecords.resolved')}</Badge>
                      )}
                    </div>
                    <div className="p-2 bg-destructive/10 text-destructive text-sm rounded mb-2">
                      {record.error_message}
                    </div>
                    <details className="text-sm">
                      <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                        {t('failedRecords.viewPayload')}
                      </summary>
                      <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto max-h-40">
                        {JSON.stringify(record.record_data, null, 2)}
                      </pre>
                    </details>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => retryMutation.mutate(record.uid)}
                      disabled={retryMutation.isPending || record.resolved}
                    >
                      <RotateCcw className="mr-1 h-3 w-3" />
                      {t('failedRecords.retry')}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(record)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
