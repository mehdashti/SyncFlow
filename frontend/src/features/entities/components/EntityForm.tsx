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
import { entitiesService } from '@/api/services'
import type { Entity } from '@/types'

const entitySchema = z.object({
  target_schema: z.string().min(1, 'Target schema is required'),
  target_table: z.string().min(1, 'Target table is required'),
  sync_enabled: z.boolean(),
  sync_interval_seconds: z.number().min(60).max(86400),
})

type EntityFormData = z.infer<typeof entitySchema>

interface EntityFormProps {
  entity: Entity
  onClose: () => void
}

export function EntityForm({ entity, onClose }: EntityFormProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<EntityFormData>({
    resolver: zodResolver(entitySchema),
    defaultValues: {
      target_schema: entity.target_schema,
      target_table: entity.target_table,
      sync_enabled: entity.sync_enabled,
      sync_interval_seconds: entity.sync_interval_seconds,
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: EntityFormData) =>
      entitiesService.update(entity.uid, data),
    onSuccess: () => {
      toast.success(t('success.updated'))
      queryClient.invalidateQueries({ queryKey: ['entities'] })
      onClose()
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const onSubmit = (data: EntityFormData) => {
    updateMutation.mutate(data)
  }

  const syncEnabled = watch('sync_enabled')

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg">{t('entities.edit')}</CardTitle>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="target_schema">{t('entities.form.targetSchema')}</Label>
              <Input id="target_schema" {...register('target_schema')} />
              {errors.target_schema && (
                <p className="text-sm text-destructive">{errors.target_schema.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="target_table">{t('entities.form.targetTable')}</Label>
              <Input id="target_table" {...register('target_table')} />
              {errors.target_table && (
                <p className="text-sm text-destructive">{errors.target_table.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="sync_interval_seconds">{t('entities.form.syncInterval')}</Label>
            <Input
              id="sync_interval_seconds"
              type="number"
              {...register('sync_interval_seconds', { valueAsNumber: true })}
            />
            {errors.sync_interval_seconds && (
              <p className="text-sm text-destructive">{errors.sync_interval_seconds.message}</p>
            )}
            <p className="text-xs text-muted-foreground">
              {t('entities.form.syncIntervalHint')}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Switch
              id="sync_enabled"
              checked={syncEnabled}
              onCheckedChange={(checked) => setValue('sync_enabled', checked)}
            />
            <Label htmlFor="sync_enabled">{t('entities.form.syncEnabled')}</Label>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? t('common.saving') : t('common.save')}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
