import { createFileRoute } from '@tanstack/react-router'
import { FailedRecordsPage } from '@/features/sync/pages/FailedRecordsPage'

export const Route = createFileRoute('/_app/failed-records')({
  component: FailedRecordsPage,
})
