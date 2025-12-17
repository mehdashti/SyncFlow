import { createFileRoute } from '@tanstack/react-router'
import { SchedulesPage } from '@/features/schedules/pages/SchedulesPage'

export const Route = createFileRoute('/_app/schedules')({
  component: SchedulesPage,
})
