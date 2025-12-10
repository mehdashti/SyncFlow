import { useTranslation } from 'react-i18next'
import { Plus, Edit, Trash2 } from 'lucide-react'
import { PageHeader } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function EntitiesPage() {
  const { t } = useTranslation()

  // Mock data
  const entities = [
    {
      uid: '1',
      entity_name: 'inventory_items',
      source_system: 'ifs',
      business_key_fields: ['item_no', 'warehouse'],
      parent_refs: [{ parent_entity: 'warehouses', ref_field: 'warehouse_id' }],
      sync_enabled: true,
    },
    {
      uid: '2',
      entity_name: 'customers',
      source_system: 'ifs',
      business_key_fields: ['customer_id'],
      parent_refs: [],
      sync_enabled: true,
    },
    {
      uid: '3',
      entity_name: 'work_orders',
      source_system: 'ifs',
      business_key_fields: ['wo_no', 'release_no'],
      parent_refs: [{ parent_entity: 'inventory_items', ref_field: 'part_no' }],
      sync_enabled: false,
    },
  ]

  return (
    <div>
      <PageHeader
        title={t('entity.title')}
        actions={
          <Button>
            <Plus className="me-2 h-4 w-4" />
            {t('entity.createEntity')}
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-700">
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('sync.entityName')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('entity.sourceSystem')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('entity.businessKeyFields')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('entity.parentRefs')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('entity.syncEnabled')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              {entities.map((entity) => (
                <tr
                  key={entity.uid}
                  className="border-b border-neutral-100 last:border-0 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                >
                  <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">
                    {entity.entity_name}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="secondary">{entity.source_system}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {entity.business_key_fields.map((field) => (
                        <Badge key={field} variant="outline">
                          {field}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-500">
                    {entity.parent_refs.length > 0
                      ? entity.parent_refs.map((ref) => ref.parent_entity).join(', ')
                      : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={entity.sync_enabled ? 'success' : 'secondary'}>
                      {entity.sync_enabled ? t('status.enabled') : t('status.disabled')}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
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
