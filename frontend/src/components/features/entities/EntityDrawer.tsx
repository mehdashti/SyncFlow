import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, X } from 'lucide-react'
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
import { Badge } from '@/components/ui/badge'
import type { Entity, CreateEntityRequest, ParentRef } from '@/api/types'

interface EntityDrawerProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: CreateEntityRequest) => void
  entity?: Entity | null
}

export function EntityDrawer({ open, onClose, onSubmit, entity }: EntityDrawerProps) {
  const { t } = useTranslation()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<CreateEntityRequest>({
    entity_name: '',
    source_system: 'ifs',
    business_key_fields: [],
    parent_refs: [],
    sync_enabled: true,
  })
  const [newKeyField, setNewKeyField] = useState('')
  const [newParentRef, setNewParentRef] = useState<ParentRef>({
    parent_entity: '',
    ref_field: '',
    parent_field: '',
  })

  useEffect(() => {
    if (entity) {
      setFormData({
        entity_name: entity.entity_name,
        source_system: entity.source_system,
        business_key_fields: entity.business_key_fields,
        parent_refs: entity.parent_refs,
        sync_enabled: entity.sync_enabled,
      })
    } else {
      setFormData({
        entity_name: '',
        source_system: 'ifs',
        business_key_fields: [],
        parent_refs: [],
        sync_enabled: true,
      })
    }
  }, [entity, open])

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

  const addKeyField = () => {
    if (newKeyField && !formData.business_key_fields.includes(newKeyField)) {
      setFormData({
        ...formData,
        business_key_fields: [...formData.business_key_fields, newKeyField],
      })
      setNewKeyField('')
    }
  }

  const removeKeyField = (field: string) => {
    setFormData({
      ...formData,
      business_key_fields: formData.business_key_fields.filter((f) => f !== field),
    })
  }

  const addParentRef = () => {
    if (newParentRef.parent_entity && newParentRef.ref_field) {
      setFormData({
        ...formData,
        parent_refs: [...(formData.parent_refs || []), newParentRef],
      })
      setNewParentRef({ parent_entity: '', ref_field: '', parent_field: '' })
    }
  }

  const removeParentRef = (index: number) => {
    setFormData({
      ...formData,
      parent_refs: formData.parent_refs?.filter((_, i) => i !== index),
    })
  }

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {entity ? t('entity.editEntity') : t('entity.createEntity')}
          </SheetTitle>
          <SheetDescription>
            Configure entity synchronization settings
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="mt-6 space-y-6">
          {/* Entity Name */}
          <div className="space-y-2">
            <Label htmlFor="entity_name">{t('sync.entityName')}</Label>
            <Input
              id="entity_name"
              placeholder="e.g., inventory_items"
              value={formData.entity_name}
              onChange={(e) =>
                setFormData({ ...formData, entity_name: e.target.value })
              }
              disabled={!!entity}
            />
          </div>

          {/* Source System */}
          <div className="space-y-2">
            <Label htmlFor="source_system">{t('entity.sourceSystem')}</Label>
            <Input
              id="source_system"
              placeholder="e.g., ifs"
              value={formData.source_system}
              onChange={(e) =>
                setFormData({ ...formData, source_system: e.target.value })
              }
            />
          </div>

          {/* Business Key Fields */}
          <div className="space-y-2">
            <Label>{t('entity.businessKeyFields')}</Label>
            <div className="flex gap-2">
              <Input
                placeholder="Add field name"
                value={newKeyField}
                onChange={(e) => setNewKeyField(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyField())}
              />
              <Button type="button" variant="outline" onClick={addKeyField}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-1 mt-2">
              {formData.business_key_fields.map((field) => (
                <Badge key={field} variant="secondary" className="gap-1">
                  {field}
                  <button
                    type="button"
                    onClick={() => removeKeyField(field)}
                    className="hover:text-error-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Parent References */}
          <div className="space-y-2">
            <Label>{t('entity.parentRefs')}</Label>
            <div className="space-y-2 p-3 border rounded-md bg-neutral-50 dark:bg-neutral-800/50">
              <Input
                placeholder={t('entity.parentEntity')}
                value={newParentRef.parent_entity}
                onChange={(e) =>
                  setNewParentRef({ ...newParentRef, parent_entity: e.target.value })
                }
              />
              <Input
                placeholder={t('entity.refField')}
                value={newParentRef.ref_field}
                onChange={(e) =>
                  setNewParentRef({ ...newParentRef, ref_field: e.target.value })
                }
              />
              <Input
                placeholder={t('entity.parentField')}
                value={newParentRef.parent_field}
                onChange={(e) =>
                  setNewParentRef({ ...newParentRef, parent_field: e.target.value })
                }
              />
              <Button type="button" variant="outline" size="sm" onClick={addParentRef}>
                <Plus className="h-4 w-4 me-1" />
                Add Reference
              </Button>
            </div>
            {formData.parent_refs && formData.parent_refs.length > 0 && (
              <div className="space-y-2 mt-2">
                {formData.parent_refs.map((ref, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 border rounded bg-white dark:bg-neutral-900"
                  >
                    <div className="text-sm">
                      <span className="font-medium">{ref.parent_entity}</span>
                      <span className="text-neutral-500">
                        {' '}
                        ({ref.ref_field} → {ref.parent_field || ref.ref_field})
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeParentRef(index)}
                      className="text-neutral-500 hover:text-error-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sync Enabled */}
          <div className="flex items-center justify-between">
            <Label htmlFor="sync_enabled">{t('entity.syncEnabled')}</Label>
            <Switch
              id="sync_enabled"
              checked={formData.sync_enabled}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, sync_enabled: checked })
              }
            />
          </div>

          <SheetFooter className="pt-6">
            <Button type="button" variant="outline" onClick={onClose}>
              {t('common.cancel')}
            </Button>
            <Button
              type="submit"
              disabled={!formData.entity_name || formData.business_key_fields.length === 0 || isSubmitting}
            >
              {isSubmitting ? t('common.loading') : t('common.save')}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  )
}
