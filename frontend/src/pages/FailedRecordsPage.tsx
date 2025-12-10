import { useTranslation } from 'react-i18next'
import { RefreshCw, Check, Eye } from 'lucide-react'
import { PageHeader } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function FailedRecordsPage() {
  const { t } = useTranslation()

  // Mock data
  const failedRecords = [
    {
      uid: '1',
      entity_name: 'inventory_items',
      stage_failed: 'NORMALIZE',
      error_type: 'VALIDATION_ERROR',
      error_message: "Required field 'item_number' is missing",
      retry_count: 2,
      max_retries: 3,
      is_resolved: false,
      created_at: '2025-12-08 14:30:00',
    },
    {
      uid: '2',
      entity_name: 'customers',
      stage_failed: 'MERGE',
      error_type: 'DUPLICATE_KEY',
      error_message: 'Duplicate business key found',
      retry_count: 3,
      max_retries: 3,
      is_resolved: false,
      created_at: '2025-12-08 12:15:00',
    },
    {
      uid: '3',
      entity_name: 'work_orders',
      stage_failed: 'RESOLVE',
      error_type: 'MISSING_PARENT',
      error_message: 'Parent entity not found',
      retry_count: 1,
      max_retries: 3,
      is_resolved: true,
      created_at: '2025-12-07 10:00:00',
    },
  ]

  return (
    <div>
      <PageHeader
        title={t('monitoring.failedRecords')}
        actions={
          <Button variant="outline">
            <RefreshCw className="me-2 h-4 w-4" />
            {t('sync.retryFailed')}
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
                  {t('monitoring.stageFailed')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('monitoring.errorType')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('monitoring.errorMessage')}
                </th>
                <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                  {t('monitoring.retryCount')}
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
              {failedRecords.map((record) => (
                <tr
                  key={record.uid}
                  className="border-b border-neutral-100 last:border-0 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                >
                  <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">
                    {record.entity_name}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="secondary">{record.stage_failed}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="error">{record.error_type}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral-600 dark:text-neutral-400 max-w-xs truncate">
                    {record.error_message}
                  </td>
                  <td className="px-4 py-3">
                    <span className={record.retry_count >= record.max_retries ? 'text-error-600' : ''}>
                      {record.retry_count}/{record.max_retries}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={record.is_resolved ? 'success' : 'error'}>
                      {record.is_resolved ? t('monitoring.isResolved') : t('status.failed')}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" className="h-8 w-8" title="View Details">
                        <Eye className="h-4 w-4" />
                      </Button>
                      {!record.is_resolved && (
                        <>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            title={t('common.retry')}
                            disabled={record.retry_count >= record.max_retries}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-success-600"
                            title={t('monitoring.markResolved')}
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                        </>
                      )}
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
