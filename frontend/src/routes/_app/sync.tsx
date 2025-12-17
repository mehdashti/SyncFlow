import { createFileRoute } from '@tanstack/react-router'
import { SyncPage } from '@/features/sync/pages/SyncPage'

export const Route = createFileRoute('/_app/sync')({
  component: SyncPage,
})
