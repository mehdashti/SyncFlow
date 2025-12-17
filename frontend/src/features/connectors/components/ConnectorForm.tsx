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
import { connectorsService } from '@/api/services'
import type { Connector } from '@/types'

const connectorSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  base_url: z.string().url('Must be a valid URL'),
  api_key: z.string().optional(),
  is_active: z.boolean(),
})

type ConnectorFormData = z.infer<typeof connectorSchema>

interface ConnectorFormProps {
  connector: Connector | null
  onClose: () => void
}

export function ConnectorForm({ connector, onClose }: ConnectorFormProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const isEdit = !!connector

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ConnectorFormData>({
    resolver: zodResolver(connectorSchema),
    defaultValues: {
      name: connector?.name || '',
      base_url: connector?.base_url || '',
      api_key: '',
      is_active: connector?.is_active ?? true,
    },
  })

  const createMutation = useMutation({
    mutationFn: connectorsService.create,
    onSuccess: () => {
      toast.success(t('success.created'))
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
      onClose()
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ uid, data }: { uid: string; data: Partial<ConnectorFormData> }) =>
      connectorsService.update(uid, data),
    onSuccess: () => {
      toast.success(t('success.updated'))
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
      onClose()
    },
    onError: () => {
      toast.error(t('errors.serverError'))
    },
  })

  const onSubmit = (data: ConnectorFormData) => {
    if (isEdit) {
      updateMutation.mutate({ uid: connector.uid, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const isActive = watch('is_active')

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg">
          {isEdit ? t('connectors.edit') : t('connectors.create')}
        </CardTitle>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">{t('connectors.form.name')}</Label>
              <Input
                id="name"
                {...register('name')}
                placeholder={t('connectors.form.namePlaceholder')}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="base_url">{t('connectors.form.baseUrl')}</Label>
              <Input
                id="base_url"
                {...register('base_url')}
                placeholder="https://apismith.example.com"
              />
              {errors.base_url && (
                <p className="text-sm text-destructive">{errors.base_url.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="api_key">{t('connectors.form.apiKey')}</Label>
            <Input
              id="api_key"
              type="password"
              {...register('api_key')}
              placeholder={isEdit ? t('connectors.form.apiKeyPlaceholder') : ''}
            />
            {isEdit && (
              <p className="text-xs text-muted-foreground">
                {t('connectors.form.apiKeyHint')}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Switch
              id="is_active"
              checked={isActive}
              onCheckedChange={(checked) => setValue('is_active', checked)}
            />
            <Label htmlFor="is_active">{t('connectors.form.active')}</Label>
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
