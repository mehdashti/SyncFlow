import { createFileRoute } from '@tanstack/react-router'
import { ConnectorsPage } from '@/features/connectors/pages/ConnectorsPage'

export const Route = createFileRoute('/_app/connectors')({
  component: ConnectorsPage,
})
