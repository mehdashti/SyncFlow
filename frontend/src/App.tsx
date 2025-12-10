import { Suspense } from 'react'
import { RouterProvider } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/toast'
import { router } from '@/routes'
import { useTheme } from '@/hooks/useTheme'
import { useLocale } from '@/hooks/useLocale'
import '@/i18n'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

// Theme and Locale initializer component
function AppInitializer({ children }: { children: React.ReactNode }) {
  useTheme()
  useLocale()
  return <>{children}</>
}

// Loading fallback
function LoadingFallback() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-neutral-500">Loading...</div>
    </div>
  )
}

function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <AppInitializer>
            <RouterProvider router={router} />
            <Toaster position="top-right" />
          </AppInitializer>
        </TooltipProvider>
      </QueryClientProvider>
    </Suspense>
  )
}

export default App
