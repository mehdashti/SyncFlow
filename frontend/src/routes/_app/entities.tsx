import { createFileRoute } from '@tanstack/react-router'
import { EntitiesPage } from '@/features/entities/pages/EntitiesPage'

export const Route = createFileRoute('/_app/entities')({
  component: EntitiesPage,
})
