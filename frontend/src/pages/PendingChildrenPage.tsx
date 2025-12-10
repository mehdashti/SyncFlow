import { useTranslation } from 'react-i18next'
import { Eye } from 'lucide-react'
import { PageHeader } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function PendingChildrenPage() {
  const { t } = useTranslation()

  // Mock data
  const pendingChildren = [
    {
      uid: '1',
      child_entity: 'inventory_items',
      parent_entity: 'warehouses',
      parent_business_key: 'WH001',
      missing_parent_field: 'warehouse_id',
      created_at: '2025-12-08 14:30:00',
    },
    {
      uid: '2',
      child_entity: 'work_orders',
      parent_entity: 'inventory_items',
      parent_business_key: 'ITEM-12345',
      missing_parent_field: 'part_no',
      created_at: '2025-12-08 12:15:00',
    },
    {
      uid: '3',
      child_entity: 'order_lines',
      parent_entity: 'orders',
      parent_business_key: 'ORD-789',
      missing_parent_field: 'order_id',
      created_at: '2025-12-07 10:00:00',
    },
  ]

  return (
    <div>
      <PageHeader title={t('monitoring.pendingChildren')} />

      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-700">
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('monitoring.childEntity')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('monitoring.parentEntity')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('monitoring.missingParent')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  Business Key
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  Created At
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              {pendingChildren.map((record) => (
                <tr
                  key={record.uid}
                  className="border-b border-neutral-100 last:border-0 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                >
                  <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">
                    {record.child_entity}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="secondary">{record.parent_entity}</Badge>
                  </td>
                  <td className="px-4 py-3 font-mono text-sm text-neutral-600 dark:text-neutral-400">
                    {record.missing_parent_field}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="warning">{record.parent_business_key}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-500">
                    {record.created_at}
                  </td>
                  <td className="px-4 py-3">
                    <Button variant="ghost" size="icon" className="h-8 w-8" title="View Details">
                      <Eye className="h-4 w-4" />
                    </Button>
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
