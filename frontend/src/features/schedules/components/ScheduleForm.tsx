import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { schedulesService } from '@/api/services'
import type { Schedule, Entity } from '@/types'

const scheduleSchema = z.object({
  entity_uid: z.string().min(1, 'Entity is required'),
  cron_expression: z.string().min(1, 'Cron expression is required'),
  is_active: z.boolean(),
})

type ScheduleFormData = z.infer<typeof scheduleSchema>

interface ScheduleFormProps {
  schedule: Schedule | null
  entities: Entity[]
  onClose: () => void
}

export function ScheduleForm({ schedule, entities, onClose }: ScheduleFormProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const isEdit = !!schedule

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ScheduleFormData>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: {
      entity_uid: schedule?.entity_uid || '',
      cron_expression: schedule?.cron_expression || '0 * * * *',
      is_active: schedule?.is_active ?? true,
    },
  })

  const createMutation = useMutation({
    mutationFn: schedulesService.create,
    onSuccess: () => {
      toast.success(t('success.created'))
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      onClose()
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ uid, data }: { uid: string; data: { cron_expression?: string; is_active?: boolean } }) =>
      schedulesService.update(uid, data),
    onSuccess: () => {
      toast.success(t('success.updated'))
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      onClose()
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const onSubmit = (data: ScheduleFormData) => {
    if (isEdit) {
      updateMutation.mutate({
        uid: schedule.uid,
        data: {
          cron_expression: data.cron_expression,
          is_active: data.is_active,
        },
      })
    } else {
      createMutation.mutate({
        entity_uid: data.entity_uid,
        cron_expression: data.cron_expression,
        is_active: data.is_active,
      })
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const isActive = watch('is_active')

  const cronPresets = [
    { label: t('schedules.cron.everyMinute'), value: '* * * * *' },
    { label: t('schedules.cron.everyHour'), value: '0 * * * *' },
    { label: t('schedules.cron.everyDay'), value: '0 0 * * *' },
    { label: t('schedules.cron.everyWeek'), value: '0 0 * * 0' },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg">
          {isEdit ? t('schedules.edit') : t('schedules.create')}
        </CardTitle>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="entity_uid">{t('schedules.form.entity')}</Label>
              <select
                id="entity_uid"
                {...register('entity_uid')}
                disabled={isEdit}
                className="flex h-9 w-full rounded-[var(--radius)] border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">{t('schedules.form.selectEntity')}</option>
                {entities.map((entity) => (
                  <option key={entity.uid} value={entity.uid}>
                    {entity.api_name}
                  </option>
                ))}
              </select>
              {errors.entity_uid && (
                <p className="text-sm text-destructive">{errors.entity_uid.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="cron_expression">{t('schedules.form.cronExpression')}</Label>
              <Input
                id="cron_expression"
                {...register('cron_expression')}
                placeholder="0 * * * *"
                className="font-mono"
              />
              {errors.cron_expression && (
                <p className="text-sm text-destructive">{errors.cron_expression.message}</p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {cronPresets.map((preset) => (
              <Button
                key={preset.value}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setValue('cron_expression', preset.value)}
              >
                {preset.label}
              </Button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Switch
              id="is_active"
              checked={isActive}
              onCheckedChange={(checked) => setValue('is_active', checked)}
            />
            <Label htmlFor="is_active">{t('schedules.form.enabled')}</Label>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? t('common.saving') : isEdit ? t('common.save') : t('common.create')}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
