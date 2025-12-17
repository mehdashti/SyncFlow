import { Suspense, useEffect } from 'react'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { routeTree } from './routeTree.gen'
import { useThemeStore } from './store/themeStore'
import './lib/i18n'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

// Create router
const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

// Loading fallback
function LoadingFallback() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  )
}

// Theme initializer
function ThemeInitializer({ children }: { children: React.ReactNode }) {
  const { theme } = useThemeStore()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return <>{children}</>
}

function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <QueryClientProvider client={queryClient}>
        <ThemeInitializer>
          <RouterProvider router={router} />
          <Toaster position="top-center" richColors />
        </ThemeInitializer>
      </QueryClientProvider>
    </Suspense>
  )
}

export default App
