import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, Search, Pencil, Trash2, Play, ChevronDown, Database } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { entitiesService, connectorsService } from '@/api/services'
import type { Entity } from '@/types'
import { EntityForm } from '../components/EntityForm'
import { formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

type FormMode = 'closed' | 'edit'

export function EntitiesPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [formMode, setFormMode] = useState<FormMode>('closed')
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)

  const { data: entities = [], isLoading, refetch } = useQuery({
    queryKey: ['entities'],
    queryFn: entitiesService.getAll,
  })

  const { data: connectors = [] } = useQuery({
    queryKey: ['connectors'],
    queryFn: connectorsService.getAll,
  })

  const deleteMutation = useMutation({
    mutationFn: entitiesService.delete,
    onSuccess: () => {
      toast.success(t('success.deleted'))
      queryClient.invalidateQueries({ queryKey: ['entities'] })
      handleCloseForm()
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const syncMutation = useMutation({
    mutationFn: entitiesService.triggerSync,
    onSuccess: () => {
      toast.success(t('entities.syncStarted'))
      queryClient.invalidateQueries({ queryKey: ['entities'] })
      queryClient.invalidateQueries({ queryKey: ['sync-runs'] })
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const filteredEntities = entities.filter((entity) =>
    entity.api_name.toLowerCase().includes(search.toLowerCase()) ||
    entity.slug.toLowerCase().includes(search.toLowerCase())
  )

  const handleEdit = (entity: Entity) => {
    if (formMode === 'edit' && selectedEntity?.uid === entity.uid) {
      handleCloseForm()
    } else {
      setSelectedEntity(entity)
      setFormMode('edit')
    }
  }

  const handleCloseForm = () => {
    setFormMode('closed')
    setSelectedEntity(null)
  }

  const handleDelete = (entity: Entity) => {
    if (window.confirm(t('entities.deleteConfirm'))) {
      deleteMutation.mutate(entity.uid)
    }
  }

  const getConnectorName = (connectorUid: string) => {
    const connector = connectors.find((c) => c.uid === connectorUid)
    return connector?.name || connectorUid
  }

  const isSelected = (entity: Entity) =>
    formMode === 'edit' && selectedEntity?.uid === entity.uid

  const getSyncStatusBadge = (status: Entity['last_sync_status']) => {
    if (status === 'success') {
      return <Badge variant="success">{t('sync.status.completed')}</Badge>
    }
    if (status === 'failed') {
      return <Badge variant="destructive">{t('sync.status.failed')}</Badge>
    }
    if (status === 'running') {
      return <Badge variant="default">{t('sync.status.running')}</Badge>
    }
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('entities.title')}</h1>
          <p className="text-muted-foreground">{t('entities.description')}</p>
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

      {/* Entities List */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="space-y-2">
                <div className="h-4 w-1/2 bg-muted rounded" />
                <div className="h-3 w-1/3 bg-muted rounded" />
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : filteredEntities.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{t('entities.noEntities')}</p>
            <p className="text-sm text-muted-foreground mt-2">
              {t('entities.discoverHint')}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredEntities.map((entity) => (
            <div key={entity.uid} className="space-y-2">
              {/* Entity Card */}
              <Card
                className={cn(
                  'group relative transition-all',
                  isSelected(entity) && 'ring-2 ring-primary border-primary'
                )}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <ChevronDown
                        className={cn(
                          'h-4 w-4 text-muted-foreground transition-transform',
                          isSelected(entity) && 'rotate-180 text-primary'
                        )}
                      />
                      <div>
                        <CardTitle className="text-lg">{entity.api_name}</CardTitle>
                        <p className="text-sm text-muted-foreground font-mono">
                          {entity.target_schema}.{entity.target_table}
                        </p>
                      </div>
                    </div>
                    <Badge variant={entity.sync_enabled ? 'success' : 'secondary'}>
                      {entity.sync_enabled ? t('status.active') : t('status.inactive')}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">{t('entities.connector')}:</span>
                    <Badge variant="outline">{entity.connector_name || getConnectorName(entity.connector_uid)}</Badge>
                  </div>

                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>{t('entities.syncMode.label')}: {entity.delta_strategy}</span>
                    {entity.last_sync_at_utc && (
                      <span>
                        {t('entities.lastSynced')}: {formatRelativeTime(entity.last_sync_at_utc)}
                      </span>
                    )}
                  </div>

                  {entity.last_sync_status && (
                    <div className="flex items-center gap-2">
                      {getSyncStatusBadge(entity.last_sync_status)}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => syncMutation.mutate(entity.uid)}
                      disabled={syncMutation.isPending || !entity.sync_enabled}
                    >
                      <Play className="mr-1 h-3 w-3" />
                      {t('entities.syncNow')}
                    </Button>
                    <Button
                      variant={isSelected(entity) ? 'default' : 'ghost'}
                      size="icon"
                      onClick={() => handleEdit(entity)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(entity)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Inline Edit Form - Below Selected Card */}
              {isSelected(entity) && (
                <div className="ml-6 border-l-2 border-primary pl-4">
                  <EntityForm entity={entity} onClose={handleCloseForm} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
