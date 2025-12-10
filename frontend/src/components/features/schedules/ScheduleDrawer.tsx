import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { Schedule, CreateScheduleRequest } from '@/api/types'

interface ScheduleDrawerProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: CreateScheduleRequest) => void
  schedule?: Schedule | null
}

export function ScheduleDrawer({ open, onClose, onSubmit, schedule }: ScheduleDrawerProps) {
  const { t } = useTranslation()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<CreateScheduleRequest>({
    entity_name: '',
    source_system: 'ifs',
    time_window_start: '19:00:00',
    time_window_end: '07:00:00',
    days_to_complete: 7,
    rows_per_day: undefined,
    total_rows_estimate: undefined,
    is_enabled: true,
  })

  useEffect(() => {
    if (schedule) {
      setFormData({
        entity_name: schedule.entity_name,
        source_system: schedule.source_system,
        time_window_start: schedule.time_window_start,
        time_window_end: schedule.time_window_end,
        days_to_complete: schedule.days_to_complete,
        rows_per_day: schedule.rows_per_day,
        total_rows_estimate: schedule.total_rows_estimate,
        is_enabled: schedule.is_enabled,
      })
    } else {
      setFormData({
        entity_name: '',
        source_system: 'ifs',
        time_window_start: '19:00:00',
        time_window_end: '07:00:00',
        days_to_complete: 7,
        rows_per_day: undefined,
        total_rows_estimate: undefined,
        is_enabled: true,
      })
    }
  }, [schedule, open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      await onSubmit(formData)
      onClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  // Mock entities list
  const entities = [
    'inventory_items',
    'customers',
    'work_orders',
    'sales_orders',
    'purchase_orders',
  ]

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>
            {schedule ? t('schedule.editSchedule') : t('schedule.createSchedule')}
          </SheetTitle>
          <SheetDescription>
            Configure background synchronization schedule
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="mt-6 space-y-6">
          {/* Entity Name */}
          <div className="space-y-2">
            <Label htmlFor="entity_name">{t('sync.entityName')}</Label>
            <Select
              value={formData.entity_name}
              onValueChange={(value) =>
                setFormData({ ...formData, entity_name: value })
              }
              disabled={!!schedule}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select entity" />
              </SelectTrigger>
              <SelectContent>
                {entities.map((entity) => (
                  <SelectItem key={entity} value={entity}>
                    {entity}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Source System */}
          <div className="space-y-2">
            <Label htmlFor="source_system">{t('entity.sourceSystem')}</Label>
            <Input
              id="source_system"
              value={formData.source_system}
              onChange={(e) =>
                setFormData({ ...formData, source_system: e.target.value })
              }
            />
          </div>

          {/* Time Window */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="time_window_start">{t('schedule.windowStart')}</Label>
              <Input
                id="time_window_start"
                type="time"
                value={formData.time_window_start.slice(0, 5)}
                onChange={(e) =>
                  setFormData({ ...formData, time_window_start: e.target.value + ':00' })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="time_window_end">{t('schedule.windowEnd')}</Label>
              <Input
                id="time_window_end"
                type="time"
                value={formData.time_window_end.slice(0, 5)}
                onChange={(e) =>
                  setFormData({ ...formData, time_window_end: e.target.value + ':00' })
                }
              />
            </div>
          </div>

          {/* Days to Complete */}
          <div className="space-y-2">
            <Label htmlFor="days_to_complete">{t('schedule.daysToComplete')}</Label>
            <Input
              id="days_to_complete"
              type="number"
              min={1}
              max={30}
              value={formData.days_to_complete}
              onChange={(e) =>
                setFormData({ ...formData, days_to_complete: parseInt(e.target.value) || 1 })
              }
            />
          </div>

          {/* Rows per Day */}
          <div className="space-y-2">
            <Label htmlFor="rows_per_day">{t('schedule.rowsPerDay')}</Label>
            <Input
              id="rows_per_day"
              type="number"
              min={0}
              placeholder="Auto-calculated if empty"
              value={formData.rows_per_day || ''}
              onChange={(e) =>
                setFormData({ ...formData, rows_per_day: parseInt(e.target.value) || undefined })
              }
            />
          </div>

          {/* Total Rows Estimate */}
          <div className="space-y-2">
            <Label htmlFor="total_rows_estimate">{t('schedule.totalRows')}</Label>
            <Input
              id="total_rows_estimate"
              type="number"
              min={0}
              placeholder="Optional"
              value={formData.total_rows_estimate || ''}
              onChange={(e) =>
                setFormData({ ...formData, total_rows_estimate: parseInt(e.target.value) || undefined })
              }
            />
          </div>

          {/* Enabled */}
          <div className="flex items-center justify-between">
            <Label htmlFor="is_enabled">{t('status.enabled')}</Label>
            <Switch
              id="is_enabled"
              checked={formData.is_enabled}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, is_enabled: checked })
              }
            />
          </div>

          <SheetFooter className="pt-6">
            <Button type="button" variant="outline" onClick={onClose}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={!formData.entity_name || isSubmitting}>
              {isSubmitting ? t('common.loading') : t('common.save')}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  )
}
