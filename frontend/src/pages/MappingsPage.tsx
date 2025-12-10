import { useTranslation } from 'react-i18next'
import { Plus, Edit, Trash2 } from 'lucide-react'
import { PageHeader } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function MappingsPage() {
  const { t } = useTranslation()

  // Mock data
  const mappings = [
    {
      uid: '1',
      entity_name: 'inventory_items',
      source_field: 'ITEM_NO',
      target_field: 'item_number',
      transformation: 'uppercase',
      is_required: true,
    },
    {
      uid: '2',
      entity_name: 'inventory_items',
      source_field: 'DESCRIPTION',
      target_field: 'description',
      transformation: null,
      is_required: false,
    },
    {
      uid: '3',
      entity_name: 'customers',
      source_field: 'CUSTOMER_ID',
      target_field: 'customer_id',
      transformation: null,
      is_required: true,
    },
  ]

  return (
    <div>
      <PageHeader
        title={t('mapping.title')}
        actions={
          <Button>
            <Plus className="me-2 h-4 w-4" />
            {t('mapping.createMapping')}
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
                  {t('mapping.sourceField')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('mapping.targetField')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('mapping.transformation')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('mapping.isRequired')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              {mappings.map((mapping) => (
                <tr
                  key={mapping.uid}
                  className="border-b border-neutral-100 last:border-0 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                >
                  <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">
                    {mapping.entity_name}
                  </td>
                  <td className="px-4 py-3 font-mono text-sm">{mapping.source_field}</td>
                  <td className="px-4 py-3 font-mono text-sm">{mapping.target_field}</td>
                  <td className="px-4 py-3">
                    {mapping.transformation ? (
                      <Badge variant="secondary">{mapping.transformation}</Badge>
                    ) : (
                      <span className="text-neutral-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {mapping.is_required ? (
                      <Badge variant="warning">{t('mapping.isRequired')}</Badge>
                    ) : (
                      <span className="text-neutral-400">-</span>
                    )}
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
