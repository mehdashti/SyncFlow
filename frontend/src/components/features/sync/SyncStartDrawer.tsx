import { useState } from 'react'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface SyncStartDrawerProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: SyncFormData) => void
}

interface SyncFormData {
  entity_name: string
  sync_type: 'full' | 'incremental'
  connector_slug?: string
}

export function SyncStartDrawer({ open, onClose, onSubmit }: SyncStartDrawerProps) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<SyncFormData>({
    entity_name: '',
    sync_type: 'full',
    connector_slug: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

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
          <SheetTitle>{t('sync.startSync')}</SheetTitle>
          <SheetDescription>
            Configure and start a new synchronization job
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

          {/* Sync Type */}
          <div className="space-y-2">
            <Label>{t('sync.syncType')}</Label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="sync_type"
                  value="full"
                  checked={formData.sync_type === 'full'}
                  onChange={() => setFormData({ ...formData, sync_type: 'full' })}
                  className="h-4 w-4 text-primary-500"
                />
                <span>{t('sync.syncFull')}</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="sync_type"
                  value="incremental"
                  checked={formData.sync_type === 'incremental'}
                  onChange={() => setFormData({ ...formData, sync_type: 'incremental' })}
                  className="h-4 w-4 text-primary-500"
                />
                <span>{t('sync.syncIncremental')}</span>
              </label>
            </div>
          </div>

          {/* APISmith Slug */}
          <div className="space-y-2">
            <Label htmlFor="connector_slug">{t('sync.connectorSlug')}</Label>
            <Input
              id="connector_slug"
              placeholder="e.g., ifs-inventory-api"
              value={formData.connector_slug}
              onChange={(e) =>
                setFormData({ ...formData, connector_slug: e.target.value })
              }
            />
          </div>

          <SheetFooter className="pt-6">
            <Button type="button" variant="outline" onClick={onClose}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={!formData.entity_name || isSubmitting}>
              {isSubmitting ? t('common.loading') : t('sync.startSync')}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  )
}
