import { useTranslation } from 'react-i18next'
import { Plus, Play, RotateCcw, Edit, Trash2 } from 'lucide-react'
import { PageHeader } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function SchedulesPage() {
  const { t } = useTranslation()

  // Mock data
  const schedulerStatus = {
    is_running: true,
    active_jobs: 5,
    next_run: '19:00',
  }

  const schedules = [
    {
      uid: '1',
      entity_name: 'inventory',
      time_window: '19:00-07:00',
      days_to_complete: 7,
      progress: 57,
      is_enabled: true,
    },
    {
      uid: '2',
      entity_name: 'customers',
      time_window: '20:00-06:00',
      days_to_complete: 5,
      progress: 28,
      is_enabled: true,
    },
    {
      uid: '3',
      entity_name: 'work_orders',
      time_window: '19:00-07:00',
      days_to_complete: 10,
      progress: 0,
      is_enabled: false,
    },
  ]

  return (
    <div>
      <PageHeader
        title={t('schedule.title')}
        actions={
          <Button>
            <Plus className="me-2 h-4 w-4" />
            {t('schedule.createSchedule')}
          </Button>
        }
      />

      {/* Scheduler Status */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div>
                <span className="text-sm text-neutral-500">{t('schedule.schedulerStatus')}</span>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant={schedulerStatus.is_running ? 'success' : 'error'}>
                    {schedulerStatus.is_running ? t('status.running') : t('status.disabled')}
                  </Badge>
                </div>
              </div>
              <div>
                <span className="text-sm text-neutral-500">{t('schedule.activeJobs')}</span>
                <p className="font-semibold text-neutral-900 dark:text-neutral-100">
                  {schedulerStatus.active_jobs}
                </p>
              </div>
              <div>
                <span className="text-sm text-neutral-500">{t('schedule.nextRun')}</span>
                <p className="font-semibold text-neutral-900 dark:text-neutral-100">
                  {schedulerStatus.next_run}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Schedules Table */}
      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-700">
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('sync.entityName')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('schedule.timeWindow')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('schedule.daysToComplete')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('schedule.progress')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  Status
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              {schedules.map((schedule) => (
                <tr
                  key={schedule.uid}
                  className="border-b border-neutral-100 last:border-0 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                >
                  <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">
                    {schedule.entity_name}
                  </td>
                  <td className="px-4 py-3">{schedule.time_window}</td>
                  <td className="px-4 py-3">{schedule.days_to_complete}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-neutral-200 rounded-full dark:bg-neutral-700">
                        <div
                          className="h-2 bg-primary-500 rounded-full"
                          style={{ width: `${schedule.progress}%` }}
                        />
                      </div>
                      <span className="text-sm text-neutral-500">{schedule.progress}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={schedule.is_enabled ? 'success' : 'secondary'}>
                      {schedule.is_enabled ? t('status.enabled') : t('status.disabled')}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" className="h-8 w-8" title={t('schedule.triggerNow')}>
                        <Play className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8" title={t('schedule.resetProgress')}>
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-error-600">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
