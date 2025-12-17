import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, RefreshCw, Search, Pencil, Trash2, Play, Pause, ChevronDown, Calendar } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { schedulesService, entitiesService } from '@/api/services'
import type { Schedule } from '@/types'
import { ScheduleForm } from '../components/ScheduleForm'
import { formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

type FormMode = 'closed' | 'create' | 'edit'

export function SchedulesPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [formMode, setFormMode] = useState<FormMode>('closed')
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null)

  const { data: schedules = [], isLoading, refetch } = useQuery({
    queryKey: ['schedules'],
    queryFn: schedulesService.getAll,
  })

  const { data: entities = [] } = useQuery({
    queryKey: ['entities'],
    queryFn: entitiesService.getAll,
  })

  const deleteMutation = useMutation({
    mutationFn: schedulesService.delete,
    onSuccess: () => {
      toast.success(t('success.deleted'))
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      handleCloseForm()
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const pauseMutation = useMutation({
    mutationFn: schedulesService.pause,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const resumeMutation = useMutation({
    mutationFn: schedulesService.resume,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const filteredSchedules = schedules.filter((schedule) => {
    const entity = entities.find((e) => e.uid === schedule.entity_uid)
    return (
      schedule.entity_name?.toLowerCase().includes(search.toLowerCase()) ||
      entity?.api_name.toLowerCase().includes(search.toLowerCase())
    )
  })

  const handleCreate = () => {
    setSelectedSchedule(null)
    setFormMode('create')
  }

  const handleEdit = (schedule: Schedule) => {
    if (formMode === 'edit' && selectedSchedule?.uid === schedule.uid) {
      handleCloseForm()
    } else {
      setSelectedSchedule(schedule)
      setFormMode('edit')
    }
  }

  const handleCloseForm = () => {
    setFormMode('closed')
    setSelectedSchedule(null)
  }

  const handleDelete = (schedule: Schedule) => {
    if (window.confirm(t('schedules.deleteConfirm'))) {
      deleteMutation.mutate(schedule.uid)
    }
  }

  const getEntityName = (schedule: Schedule) => {
    if (schedule.entity_name) return schedule.entity_name
    const entity = entities.find((e) => e.uid === schedule.entity_uid)
    return entity?.api_name || schedule.entity_uid
  }

  const isSelected = (schedule: Schedule) =>
    formMode === 'edit' && selectedSchedule?.uid === schedule.uid

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('schedules.title')}</h1>
          <p className="text-muted-foreground">{t('schedules.description')}</p>
        </div>
        <Button onClick={handleCreate} disabled={formMode === 'create'}>
          <Plus className="mr-2 h-4 w-4" />
          {t('schedules.create')}
        </Button>
      </div>

      {/* Create Form - Top */}
      {formMode === 'create' && (
        <ScheduleForm schedule={null} entities={entities} onClose={handleCloseForm} />
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

      {/* Schedules List */}
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
      ) : filteredSchedules.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{t('schedules.noSchedules')}</p>
            <Button variant="outline" className="mt-4" onClick={handleCreate}>
              <Plus className="mr-2 h-4 w-4" />
              {t('schedules.create')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredSchedules.map((schedule) => (
            <div key={schedule.uid} className="space-y-2">
              {/* Schedule Card */}
              <Card
                className={cn(
                  'group relative transition-all',
                  isSelected(schedule) && 'ring-2 ring-primary border-primary'
                )}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <ChevronDown
                        className={cn(
                          'h-4 w-4 text-muted-foreground transition-transform',
                          isSelected(schedule) && 'rotate-180 text-primary'
                        )}
                      />
                      <div>
                        <CardTitle className="text-lg">{getEntityName(schedule)}</CardTitle>
                        <p className="text-sm text-muted-foreground font-mono">
                          {schedule.cron_expression}
                        </p>
                      </div>
                    </div>
                    <Badge variant={schedule.is_active ? 'success' : 'secondary'}>
                      {schedule.is_active ? t('status.enabled') : t('status.disabled')}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">{t('schedules.entity')}:</span>
                    <Badge variant="outline">{getEntityName(schedule)}</Badge>
                  </div>

                  {schedule.next_run_at_utc && (
                    <p className="text-sm text-muted-foreground">
                      {t('schedules.nextRun')}: {formatRelativeTime(schedule.next_run_at_utc)}
                    </p>
                  )}
                  {schedule.last_run_at_utc && (
                    <p className="text-xs text-muted-foreground">
                      {t('schedules.lastRun')}: {formatRelativeTime(schedule.last_run_at_utc)}
                    </p>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        schedule.is_active
                          ? pauseMutation.mutate(schedule.uid)
                          : resumeMutation.mutate(schedule.uid)
                      }
                      disabled={pauseMutation.isPending || resumeMutation.isPending}
                    >
                      {schedule.is_active ? (
                        <>
                          <Pause className="mr-1 h-3 w-3" />
                          {t('schedules.disable')}
                        </>
                      ) : (
                        <>
                          <Play className="mr-1 h-3 w-3" />
                          {t('schedules.enable')}
                        </>
                      )}
                    </Button>
                    <Button
                      variant={isSelected(schedule) ? 'default' : 'ghost'}
                      size="icon"
                      onClick={() => handleEdit(schedule)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(schedule)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Inline Edit Form - Below Selected Card */}
              {isSelected(schedule) && (
                <div className="ml-6 border-l-2 border-primary pl-4">
                  <ScheduleForm
                    schedule={schedule}
                    entities={entities}
                    onClose={handleCloseForm}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
