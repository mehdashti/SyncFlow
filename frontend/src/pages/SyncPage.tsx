import { useTranslation } from 'react-i18next'
import { Plus } from 'lucide-react'
import { PageHeader } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function SyncPage() {
  const { t } = useTranslation()

  // Mock data
  const activeSyncs = [
    {
      batchUid: 'abc123',
      entity: 'inventory_items',
      progress: 67,
      fetched: 670,
      total: 1000,
      inserted: 500,
      updated: 170,
      failed: 0,
      startedAt: '10:45',
      duration: '2m 15s',
    },
  ]

  const syncHistory = [
    { batchUid: 'abc123...', entity: 'items', type: 'full', status: 'completed', records: 1234, date: 'Dec 8' },
    { batchUid: 'def456...', entity: 'orders', type: 'incremental', status: 'failed', records: 567, date: 'Dec 8' },
    { batchUid: 'ghi789...', entity: 'customers', type: 'full', status: 'completed', records: 890, date: 'Dec 7' },
  ]

  return (
    <div>
      <PageHeader
        title={t('sync.title')}
        actions={
          <Button>
            <Plus className="me-2 h-4 w-4" />
            {t('sync.startSync')}
          </Button>
        }
      />

      <Tabs defaultValue="active" className="w-full">
        <TabsList>
          <TabsTrigger value="active">{t('sync.activeSyncs')}</TabsTrigger>
          <TabsTrigger value="history">{t('sync.history')}</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-4">
          {activeSyncs.length > 0 ? (
            <div className="space-y-4">
              {activeSyncs.map((sync) => (
                <Card key={sync.batchUid}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-lg text-neutral-900 dark:text-neutral-100">
                          {sync.entity}
                        </span>
                        <Badge variant="info">{t('status.running')}</Badge>
                      </div>
                      <Button variant="destructive" size="sm">
                        {t('sync.stopSync')}
                      </Button>
                    </div>

                    {/* Progress bar */}
                    <div className="mb-4">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-neutral-500">{t('sync.progress')}</span>
                        <span className="font-medium">{sync.progress}%</span>
                      </div>
                      <div className="h-2 bg-neutral-200 rounded-full dark:bg-neutral-700">
                        <div
                          className="h-2 bg-primary-500 rounded-full transition-all"
                          style={{ width: `${sync.progress}%` }}
                        />
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-neutral-500">{t('sync.fetched')}</span>
                        <p className="font-medium">{sync.fetched}/{sync.total}</p>
                      </div>
                      <div>
                        <span className="text-neutral-500">{t('sync.inserted')}</span>
                        <p className="font-medium text-success-600">{sync.inserted}</p>
                      </div>
                      <div>
                        <span className="text-neutral-500">{t('sync.updated')}</span>
                        <p className="font-medium text-info-600">{sync.updated}</p>
                      </div>
                      <div>
                        <span className="text-neutral-500">{t('sync.failed')}</span>
                        <p className="font-medium text-error-600">{sync.failed}</p>
                      </div>
                    </div>

                    <div className="mt-4 text-sm text-neutral-500">
                      {t('sync.startedAt')}: {sync.startedAt} • {t('sync.duration')}: {sync.duration}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-12 text-center text-neutral-500">
                {t('common.noData')}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-200 dark:border-neutral-700">
                    <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                      {t('sync.batchUid')}
                    </th>
                    <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                      {t('sync.entityName')}
                    </th>
                    <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                      {t('sync.syncType')}
                    </th>
                    <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                      Status
                    </th>
                    <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                      {t('sync.records')}
                    </th>
                    <th className="px-4 py-3 text-start text-sm font-medium text-neutral-500">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {syncHistory.map((item, index) => (
                    <tr
                      key={index}
                      className="border-b border-neutral-100 last:border-0 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                    >
                      <td className="px-4 py-3 font-mono text-sm">{item.batchUid}</td>
                      <td className="px-4 py-3">{item.entity}</td>
                      <td className="px-4 py-3">
                        <Badge variant="secondary">{item.type}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={item.status === 'completed' ? 'success' : 'error'}>
                          {t(`status.${item.status}`)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">{item.records}</td>
                      <td className="px-4 py-3 text-neutral-500">{item.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
