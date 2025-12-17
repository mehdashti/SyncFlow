import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, RefreshCw, Search, Pencil, Trash2, Play, Radar, ChevronDown } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { connectorsService } from '@/api/services'
import type { Connector } from '@/types'
import { ConnectorForm } from '../components/ConnectorForm'
import { formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

type FormMode = 'closed' | 'create' | 'edit'

export function ConnectorsPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [formMode, setFormMode] = useState<FormMode>('closed')
  const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null)

  const { data: connectors = [], isLoading, refetch } = useQuery({
    queryKey: ['connectors'],
    queryFn: connectorsService.getAll,
  })

  const deleteMutation = useMutation({
    mutationFn: connectorsService.delete,
    onSuccess: () => {
      toast.success(t('success.deleted'))
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
      handleCloseForm()
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const testMutation = useMutation({
    mutationFn: connectorsService.test,
    onSuccess: (result) => {
      if (result.success) {
        toast.success(`${t('connectors.testSuccess')} (${result.latency_ms}ms)`)
      } else {
        toast.error(result.error_message || t('connectors.testFailed'))
      }
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const discoverMutation = useMutation({
    mutationFn: connectorsService.discover,
    onSuccess: (result) => {
      toast.success(
        `${t('connectors.discoverySuccess')}: ${result.new_entities} ${t('connectors.newEntities')}`
      )
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
      queryClient.invalidateQueries({ queryKey: ['entities'] })
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const filteredConnectors = connectors.filter((conn) =>
    conn.name.toLowerCase().includes(search.toLowerCase()) ||
    conn.base_url.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = () => {
    setSelectedConnector(null)
    setFormMode('create')
  }

  const handleEdit = (conn: Connector) => {
    if (formMode === 'edit' && selectedConnector?.uid === conn.uid) {
      handleCloseForm()
    } else {
      setSelectedConnector(conn)
      setFormMode('edit')
    }
  }

  const handleCloseForm = () => {
    setFormMode('closed')
    setSelectedConnector(null)
  }

  const handleDelete = (conn: Connector) => {
    if (window.confirm(t('connectors.deleteConfirm'))) {
      deleteMutation.mutate(conn.uid)
    }
  }

  const getStatusBadge = (conn: Connector) => {
    if (conn.last_test_success === true) {
      return <Badge variant="success">{t('connectors.status.connected')}</Badge>
    }
    if (conn.last_test_success === false) {
      return <Badge variant="destructive">{t('connectors.status.error')}</Badge>
    }
    return <Badge variant="secondary">{t('connectors.status.untested')}</Badge>
  }

  const isSelected = (conn: Connector) =>
    formMode === 'edit' && selectedConnector?.uid === conn.uid

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('connectors.title')}</h1>
        </div>
        <Button onClick={handleCreate} disabled={formMode === 'create'}>
          <Plus className="mr-2 h-4 w-4" />
          {t('connectors.create')}
        </Button>
      </div>

      {/* Create Form - Top */}
      {formMode === 'create' && (
        <ConnectorForm connector={null} onClose={handleCloseForm} />
      )}

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

      {/* Connectors List */}
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
      ) : filteredConnectors.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground">{t('common.noData')}</p>
            <Button variant="outline" className="mt-4" onClick={handleCreate}>
              <Plus className="mr-2 h-4 w-4" />
              {t('connectors.create')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredConnectors.map((conn) => (
            <div key={conn.uid} className="space-y-2">
              {/* Connector Card */}
              <Card
                className={cn(
                  'group relative transition-all',
                  isSelected(conn) && 'ring-2 ring-primary border-primary'
                )}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <ChevronDown
                        className={cn(
                          'h-4 w-4 text-muted-foreground transition-transform',
                          isSelected(conn) && 'rotate-180 text-primary'
                        )}
                      />
                      <div>
                        <CardTitle className="text-lg">{conn.name}</CardTitle>
                        <p className="text-sm text-muted-foreground font-mono">{conn.base_url}</p>
                      </div>
                    </div>
                    {getStatusBadge(conn)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={conn.is_active ? 'success' : 'secondary'}>
                      {conn.is_active ? t('status.active') : t('status.inactive')}
                    </Badge>
                  </div>
                  {conn.last_tested_at_utc && (
                    <p className="text-xs text-muted-foreground">
                      {t('connectors.lastTested')}: {formatRelativeTime(conn.last_tested_at_utc)}
                    </p>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => testMutation.mutate(conn.uid)}
                      disabled={testMutation.isPending}
                    >
                      <Play className="mr-1 h-3 w-3" />
                      {t('connectors.test')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => discoverMutation.mutate(conn.uid)}
                      disabled={discoverMutation.isPending}
                    >
                      <Radar className="mr-1 h-3 w-3" />
                      {t('connectors.discover')}
                    </Button>
                    <Button
                      variant={isSelected(conn) ? 'default' : 'ghost'}
                      size="icon"
                      onClick={() => handleEdit(conn)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(conn)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Inline Edit Form - Below Selected Card */}
              {isSelected(conn) && (
                <div className="ml-6 border-l-2 border-primary pl-4">
                  <ConnectorForm connector={conn} onClose={handleCloseForm} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
