import { createFileRoute } from '@tanstack/react-router'
import { AppShell } from '@/components/layout'

export const Route = createFileRoute('/_app')({
  component: () => <AppShell />,
})
